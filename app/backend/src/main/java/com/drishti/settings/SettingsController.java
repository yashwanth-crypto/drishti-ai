package com.drishti.settings;

import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

/**
 * The operator-tunable thresholds. Readable by anyone signed in; only an OWNER
 * can change them (enforced in SecurityConfig).
 */
@RestController
@RequestMapping("/api/settings")
public class SettingsController {

    private final SettingsRepository repository;

    public SettingsController(SettingsRepository repository) {
        this.repository = repository;
    }

    @GetMapping
    public Settings get() {
        return repository.findAll().stream().findFirst()
                .orElseGet(() -> repository.save(new Settings()));
    }

    @PutMapping
    public Settings update(@Valid @RequestBody UpdateRequest request) {
        Settings settings = get();
        settings.setDefectThreshold(request.defectThreshold());
        settings.setRulAlertThreshold(request.rulAlertThreshold());
        return repository.save(settings);
    }

    public record UpdateRequest(
            @NotNull @DecimalMin("0.0") @DecimalMax("1.0") Double defectThreshold,
            @NotNull @DecimalMin("0.0") @DecimalMax("1.0") Double rulAlertThreshold) {}
}
