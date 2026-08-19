package com.drishti.maintenance;

import com.drishti.ml.InferenceClient;
import org.springframework.web.bind.annotation.*;

import java.time.Instant;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/maintenance")
public class MaintenanceController {

    private final ToolRepository tools;
    private final SensorReadingRepository readings;
    private final InferenceClient inference;

    public MaintenanceController(ToolRepository tools,
                                 SensorReadingRepository readings,
                                 InferenceClient inference) {
        this.tools = tools;
        this.readings = readings;
        this.inference = inference;
    }

    @GetMapping("/tools")
    public List<ToolView> listTools() {
        return tools.findAllByOrderByToolRefAsc().stream()
                .map(t -> new ToolView(t, readings.findByToolRefOrderByCycleAsc(t.getToolRef())))
                .toList();
    }

    /**
     * Scores one sensor feature row and records it against a tool. Features must
     * be the 125 columns the Module 3 model was trained on -- fetch the list from
     * the inference service at GET /predict/maintenance/features.
     */
    @PostMapping("/predict")
    public SensorReading predict(@RequestBody PredictRequest request) {
        InferenceClient.MaintenanceResult result = inference.predictMaintenance(request.features());

        SensorReading reading = new SensorReading();
        reading.setToolRef(request.toolRef());
        reading.setCycle(request.cycle());
        reading.setPredictedRul(result.predicted_rul());
        reading.setWearAlert(result.wear_alert());
        reading.setTimestamp(Instant.now());
        readings.save(reading);

        tools.findByToolRef(request.toolRef()).ifPresent(tool -> {
            tool.setCurrentCycle(request.cycle());
            tool.setPredictedRulFraction(result.predicted_rul());
            tool.setStatus(statusFor(result.predicted_rul()));
            tools.save(tool);
        });

        return reading;
    }

    private static String statusFor(double rul) {
        if (rul < 0.2) return "critical";
        if (rul < 0.4) return "warning";
        return "ok";
    }

    public record PredictRequest(Integer toolRef, Integer cycle, Map<String, Double> features) {}

    public record ToolView(Tool tool, List<SensorReading> history) {}
}
