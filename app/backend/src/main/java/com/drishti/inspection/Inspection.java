package com.drishti.inspection;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "inspections")
public class Inspection {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String partId;
    private Instant timestamp;
    private String passFail;
    private String defectType;
    private Double confidence;
    private Double inferenceMs;

    @Column(columnDefinition = "text")
    private String alertHi;

    private String imagePath;

    /** Operator's correction when they disagree with the model. Null until reviewed. */
    private String operatorVerdict;
    private Boolean wasCorrect;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getPartId() { return partId; }
    public void setPartId(String partId) { this.partId = partId; }

    public Instant getTimestamp() { return timestamp; }
    public void setTimestamp(Instant timestamp) { this.timestamp = timestamp; }

    public String getPassFail() { return passFail; }
    public void setPassFail(String passFail) { this.passFail = passFail; }

    public String getDefectType() { return defectType; }
    public void setDefectType(String defectType) { this.defectType = defectType; }

    public Double getConfidence() { return confidence; }
    public void setConfidence(Double confidence) { this.confidence = confidence; }

    public Double getInferenceMs() { return inferenceMs; }
    public void setInferenceMs(Double inferenceMs) { this.inferenceMs = inferenceMs; }

    public String getAlertHi() { return alertHi; }
    public void setAlertHi(String alertHi) { this.alertHi = alertHi; }

    public String getImagePath() { return imagePath; }
    public void setImagePath(String imagePath) { this.imagePath = imagePath; }

    public String getOperatorVerdict() { return operatorVerdict; }
    public void setOperatorVerdict(String operatorVerdict) { this.operatorVerdict = operatorVerdict; }

    public Boolean getWasCorrect() { return wasCorrect; }
    public void setWasCorrect(Boolean wasCorrect) { this.wasCorrect = wasCorrect; }
}
