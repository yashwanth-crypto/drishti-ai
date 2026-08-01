package com.drishti.maintenance;

import jakarta.persistence.*;

@Entity
@Table(name = "tools")
public class Tool {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /** Tool identifier as used by the Module 3 dataset (TollIndex). */
    @Column(unique = true)
    private Integer toolRef;

    private String status;
    private Boolean seenDuringTraining;
    private Integer totalCycles;
    private Integer currentCycle;
    private Double predictedRulFraction;
    private Double actualRulFraction;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public Integer getToolRef() { return toolRef; }
    public void setToolRef(Integer toolRef) { this.toolRef = toolRef; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public Boolean getSeenDuringTraining() { return seenDuringTraining; }
    public void setSeenDuringTraining(Boolean seenDuringTraining) { this.seenDuringTraining = seenDuringTraining; }

    public Integer getTotalCycles() { return totalCycles; }
    public void setTotalCycles(Integer totalCycles) { this.totalCycles = totalCycles; }

    public Integer getCurrentCycle() { return currentCycle; }
    public void setCurrentCycle(Integer currentCycle) { this.currentCycle = currentCycle; }

    public Double getPredictedRulFraction() { return predictedRulFraction; }
    public void setPredictedRulFraction(Double predictedRulFraction) { this.predictedRulFraction = predictedRulFraction; }

    public Double getActualRulFraction() { return actualRulFraction; }
    public void setActualRulFraction(Double actualRulFraction) { this.actualRulFraction = actualRulFraction; }
}
