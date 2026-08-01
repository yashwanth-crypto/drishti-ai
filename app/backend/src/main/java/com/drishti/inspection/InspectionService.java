package com.drishti.inspection;

import com.drishti.alert.AlertService;
import com.drishti.ml.InferenceClient;
import com.drishti.settings.Settings;
import com.drishti.settings.SettingsRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Instant;
import java.util.List;
import java.util.UUID;

@Service
public class InspectionService {

    /** Model called it good, but below the owner's confidence bar. */
    public static final String REVIEW = "review";

    private final InspectionRepository repository;
    private final InferenceClient inference;
    private final AlertService alerts;
    private final SettingsRepository settings;
    private final Path imageStorage;

    public InspectionService(InspectionRepository repository,
                             InferenceClient inference,
                             AlertService alerts,
                             SettingsRepository settings,
                             @Value("${drishti.image-storage}") String imageStorage) {
        this.repository = repository;
        this.inference = inference;
        this.alerts = alerts;
        this.settings = settings;
        this.imageStorage = Paths.get(imageStorage).toAbsolutePath().normalize();
    }

    public Inspection inspect(MultipartFile image, String partId) throws IOException {
        byte[] bytes = image.getBytes();
        InferenceClient.VisionResult result = inference.predictVision(bytes, image.getOriginalFilename());

        Files.createDirectories(imageStorage);
        Path stored = imageStorage.resolve(UUID.randomUUID() + ".jpg");
        Files.write(stored, bytes);

        String verdict = applyThreshold(result);
        // A borderline pass is reported under its own alert template, so the
        // operator is told to set the part aside rather than send it onward.
        String alertCode = REVIEW.equals(verdict) ? "needs_review" : result.defect_type();

        Inspection inspection = new Inspection();
        inspection.setPartId(partId);
        inspection.setTimestamp(Instant.now());
        inspection.setPassFail(verdict);
        inspection.setDefectType(result.defect_type());
        inspection.setConfidence(result.confidence());
        inspection.setInferenceMs(result.inference_ms());
        inspection.setAlertHi(alerts.generateAlert(alertCode, result.confidence(), partId));
        inspection.setImagePath(stored.toString());

        return repository.save(inspection);
    }

    /**
     * A part the model calls defective always fails. A part it calls good only
     * passes if it is confident enough; otherwise it goes to review. The
     * threshold therefore only ever makes the system stricter, never laxer.
     */
    private String applyThreshold(InferenceClient.VisionResult result) {
        if (!"pass".equals(result.pass_fail())) {
            return result.pass_fail();
        }
        double threshold = settings.findAll().stream().findFirst()
                .map(Settings::getDefectThreshold)
                .orElse(0.5);
        return result.confidence() >= threshold ? "pass" : REVIEW;
    }

    /**
     * The stored image for an inspection. Resolves under the configured storage
     * directory only, so a tampered path column can't read arbitrary files.
     */
    public byte[] imageFor(Long id) throws IOException {
        Inspection inspection = repository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("No inspection " + id));
        if (inspection.getImagePath() == null) {
            throw new IllegalArgumentException("Inspection " + id + " has no stored image");
        }
        Path path = Paths.get(inspection.getImagePath()).toAbsolutePath().normalize();
        if (!path.startsWith(imageStorage)) {
            throw new IllegalArgumentException("Image path outside storage directory");
        }
        return Files.readAllBytes(path);
    }

    public List<Inspection> list(String filter) {
        if ("pass".equals(filter) || "fail".equals(filter) || REVIEW.equals(filter)) {
            return repository.findByPassFailOrderByTimestampDesc(filter);
        }
        return repository.findAllByOrderByTimestampDesc();
    }

    public Inspection recordFeedback(Long id, String operatorVerdict) {
        Inspection inspection = repository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("No inspection " + id));
        inspection.setOperatorVerdict(operatorVerdict);
        inspection.setWasCorrect(operatorVerdict.equals(inspection.getDefectType()));
        return repository.save(inspection);
    }

    public Kpis kpis() {
        long total = repository.count();
        long passCount = repository.countByPassFail("pass");
        long failCount = repository.countByPassFail("fail");
        long reviewCount = repository.countByPassFail(REVIEW);
        double avgMs = repository.findAll().stream()
                .filter(i -> i.getInferenceMs() != null)
                .mapToDouble(Inspection::getInferenceMs)
                .average().orElse(0.0);
        double passRate = total == 0 ? 0.0 : (double) passCount / total;

        return new Kpis(total, passCount, failCount, reviewCount,
                Math.round(passRate * 10000) / 10000.0,
                Math.round(avgMs * 100) / 100.0);
    }

    public record Kpis(long totalInspections, long passCount, long failCount, long reviewCount,
                       double passRate, double avgInferenceMs) {}
}
