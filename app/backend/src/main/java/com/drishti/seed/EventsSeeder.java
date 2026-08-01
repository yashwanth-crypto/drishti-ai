package com.drishti.seed;

import com.drishti.forecast.ForecastPoint;
import com.drishti.forecast.ForecastPointRepository;
import com.drishti.inspection.Inspection;
import com.drishti.inspection.InspectionRepository;
import com.drishti.maintenance.SensorReading;
import com.drishti.maintenance.SensorReadingRepository;
import com.drishti.maintenance.Tool;
import com.drishti.maintenance.ToolRepository;
import com.drishti.settings.Settings;
import com.drishti.settings.SettingsRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Instant;
import java.time.LocalDate;
import java.time.OffsetDateTime;

/**
 * Loads the dashboard's existing events.json into the database on first run, so
 * a fresh install serves the same data the static prototype showed. Skipped once
 * a table has rows -- this never overwrites live data.
 */
@Component
public class EventsSeeder implements CommandLineRunner {

    private static final Logger log = LoggerFactory.getLogger(EventsSeeder.class);

    private final InspectionRepository inspections;
    private final ToolRepository tools;
    private final SensorReadingRepository readings;
    private final ForecastPointRepository forecasts;
    private final SettingsRepository settings;
    private final Path repoRoot;

    public EventsSeeder(InspectionRepository inspections,
                        ToolRepository tools,
                        SensorReadingRepository readings,
                        ForecastPointRepository forecasts,
                        SettingsRepository settings,
                        @Value("${drishti.repo-root}") String repoRoot) {
        this.inspections = inspections;
        this.tools = tools;
        this.readings = readings;
        this.forecasts = forecasts;
        this.settings = settings;
        this.repoRoot = Paths.get(repoRoot).toAbsolutePath().normalize();
    }

    @Override
    public void run(String... args) throws Exception {
        if (settings.count() == 0) {
            settings.save(new Settings());
        }

        Path eventsPath = repoRoot.resolve("dashboard/src/data/events.json");
        if (!Files.exists(eventsPath)) {
            log.warn("No seed file at {} -- starting with an empty database", eventsPath);
            return;
        }

        JsonNode root = new ObjectMapper().readTree(Files.readString(eventsPath));
        seedInspections(root.path("inspections"));
        seedTools(root.path("maintenance").path("tools"));
        seedForecasts(root.path("forecasting").path("categories"));
    }

    private void seedInspections(JsonNode nodes) {
        if (inspections.count() > 0 || !nodes.isArray()) return;

        for (JsonNode n : nodes) {
            Inspection i = new Inspection();
            i.setPartId(n.path("part_id").asText(null));
            i.setTimestamp(parseInstant(n.path("timestamp").asText(null)));
            i.setPassFail(n.path("pass_fail").asText(null));
            i.setDefectType(n.path("defect_type").asText(null));
            i.setConfidence(n.path("confidence").asDouble());
            i.setInferenceMs(n.path("inference_ms").asDouble());
            i.setAlertHi(n.path("alert_hi").asText(null));
            inspections.save(i);
        }
        log.info("Seeded {} inspections", inspections.count());
    }

    private void seedTools(JsonNode nodes) {
        if (tools.count() > 0 || !nodes.isArray()) return;

        for (JsonNode n : nodes) {
            Tool t = new Tool();
            int toolRef = n.path("tool_id").asInt();
            t.setToolRef(toolRef);
            t.setStatus(n.path("status").asText(null));
            t.setSeenDuringTraining(n.path("seen_during_training").asBoolean());
            t.setTotalCycles(n.path("total_cycles").asInt());
            t.setCurrentCycle(n.path("current_cycle").asInt());
            t.setPredictedRulFraction(n.path("predicted_rul_fraction").asDouble());
            t.setActualRulFraction(n.path("actual_rul_fraction").asDouble());
            tools.save(t);

            for (JsonNode h : n.path("history")) {
                SensorReading r = new SensorReading();
                r.setToolRef(toolRef);
                r.setCycle(h.path("cycle").asInt());
                r.setPredictedRul(h.path("predicted_rul").asDouble());
                r.setActualRul(h.path("actual_rul").asDouble());
                r.setWearAlert(h.path("predicted_rul").asDouble() < 0.2);
                r.setTimestamp(Instant.now());
                readings.save(r);
            }
        }
        log.info("Seeded {} tools, {} sensor readings", tools.count(), readings.count());
    }

    private void seedForecasts(JsonNode nodes) {
        if (forecasts.count() > 0 || !nodes.isArray()) return;

        for (JsonNode n : nodes) {
            String category = n.path("category").asText();
            double wape = n.path("wape_pct").asDouble();

            for (JsonNode h : n.path("history")) {
                ForecastPoint p = new ForecastPoint();
                p.setCategory(category);
                p.setWeek(LocalDate.parse(h.path("week").asText()));
                p.setActualDemand(h.path("actual_demand").asDouble());
                p.setWapePct(wape);
                forecasts.save(p);
            }
            for (JsonNode f : n.path("forecast")) {
                ForecastPoint p = new ForecastPoint();
                p.setCategory(category);
                p.setWeek(LocalDate.parse(f.path("week").asText()));
                p.setPredictedDemand(f.path("predicted_demand").asDouble());
                p.setLowerP10(f.path("lower").asDouble());
                p.setUpperP90(f.path("upper").asDouble());
                p.setWapePct(wape);
                forecasts.save(p);
            }
        }
        log.info("Seeded {} forecast points", forecasts.count());
    }

    private static Instant parseInstant(String value) {
        return value == null ? Instant.now() : OffsetDateTime.parse(value).toInstant();
    }
}
