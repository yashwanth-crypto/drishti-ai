package com.drishti.maintenance;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "sensor_readings")
public class SensorReading {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private Integer toolRef;
    private Integer cycle;
    private Double predictedRul;
    private Double actualRul;
    private Boolean wearAlert;
    private Instant timestamp;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public Integer getToolRef() { return toolRef; }
    public void setToolRef(Integer toolRef) { this.toolRef = toolRef; }

    public Integer getCycle() { return cycle; }
    public void setCycle(Integer cycle) { this.cycle = cycle; }

    public Double getPredictedRul() { return predictedRul; }
    public void setPredictedRul(Double predictedRul) { this.predictedRul = predictedRul; }

    public Double getActualRul() { return actualRul; }
    public void setActualRul(Double actualRul) { this.actualRul = actualRul; }

    public Boolean getWearAlert() { return wearAlert; }
    public void setWearAlert(Boolean wearAlert) { this.wearAlert = wearAlert; }

    public Instant getTimestamp() { return timestamp; }
    public void setTimestamp(Instant timestamp) { this.timestamp = timestamp; }
}
