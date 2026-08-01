package com.drishti.settings;

import jakarta.persistence.*;

/** Single-row table holding the operator-tunable thresholds. */
@Entity
@Table(name = "settings")
public class Settings {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /**
     * Minimum confidence required to accept a part as good. A part the model
     * calls good with less confidence than this is sent for human review rather
     * than passed — the lever against missed defects (limitation L4). Raising it
     * means more review work and fewer defects slipping through.
     */
    private Double defectThreshold = 0.5;

    /** Predicted RUL fraction below which a tool raises a maintenance alert. */
    private Double rulAlertThreshold = 0.2;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public Double getDefectThreshold() { return defectThreshold; }
    public void setDefectThreshold(Double defectThreshold) { this.defectThreshold = defectThreshold; }

    public Double getRulAlertThreshold() { return rulAlertThreshold; }
    public void setRulAlertThreshold(Double rulAlertThreshold) { this.rulAlertThreshold = rulAlertThreshold; }
}
