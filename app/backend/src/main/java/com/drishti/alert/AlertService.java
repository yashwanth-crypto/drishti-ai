package com.drishti.alert;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

/**
 * Module 2 vernacular alerts, ported from module2_vernacular_alert/src/alerts.py.
 * Reads the same templates/alerts_hi.json so the wording stays in one place;
 * the substitution is a two-field format, so calling Python for it would add a
 * network hop for no gain.
 */
@Service
public class AlertService {

    private final ObjectMapper mapper = new ObjectMapper();
    private final Path repoRoot;
    private JsonNode templates;

    public AlertService(@Value("${drishti.repo-root}") String repoRoot) {
        this.repoRoot = Paths.get(repoRoot).toAbsolutePath().normalize();
    }

    @PostConstruct
    void loadTemplates() throws IOException {
        Path path = repoRoot.resolve("module2_vernacular_alert/templates/alerts_hi.json");
        templates = mapper.readTree(Files.readString(path)).get("hi");
        if (templates == null) {
            throw new IllegalStateException("No 'hi' key in " + path);
        }
    }

    public String generateAlert(String defectCode, double confidence, String partId) {
        JsonNode entry = templates.has(defectCode) ? templates.get(defectCode) : templates.get("unknown");

        long confidencePct = Math.round(confidence * 100);
        String message = entry.get("message").asText().replace("{confidence}", String.valueOf(confidencePct));
        String alert = message + " " + entry.get("action").asText();

        return (partId == null || partId.isBlank()) ? alert : "[" + partId + "] " + alert;
    }
}
