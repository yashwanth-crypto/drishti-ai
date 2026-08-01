package com.drishti.forecast;

import jakarta.persistence.*;
import java.time.LocalDate;

/**
 * One weekly point for a product category. Recorded weeks carry actualDemand;
 * predicted weeks carry predictedDemand with a P10/P90 band. Keeping both in
 * one table lets the dashboard read a category's full series in one query.
 */
@Entity
@Table(name = "forecasts")
public class ForecastPoint {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String category;
    private LocalDate week;
    private Double actualDemand;
    private Double predictedDemand;
    private Double lowerP10;
    private Double upperP90;
    private Double wapePct;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getCategory() { return category; }
    public void setCategory(String category) { this.category = category; }

    public LocalDate getWeek() { return week; }
    public void setWeek(LocalDate week) { this.week = week; }

    public Double getActualDemand() { return actualDemand; }
    public void setActualDemand(Double actualDemand) { this.actualDemand = actualDemand; }

    public Double getPredictedDemand() { return predictedDemand; }
    public void setPredictedDemand(Double predictedDemand) { this.predictedDemand = predictedDemand; }

    public Double getLowerP10() { return lowerP10; }
    public void setLowerP10(Double lowerP10) { this.lowerP10 = lowerP10; }

    public Double getUpperP90() { return upperP90; }
    public void setUpperP90(Double upperP90) { this.upperP90 = upperP90; }

    public Double getWapePct() { return wapePct; }
    public void setWapePct(Double wapePct) { this.wapePct = wapePct; }
}
