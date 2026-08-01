package com.drishti.forecast;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import java.util.List;

public interface ForecastPointRepository extends JpaRepository<ForecastPoint, Long> {
    List<ForecastPoint> findByCategoryOrderByWeekAsc(String category);

    @Query("select distinct f.category from ForecastPoint f order by f.category")
    List<String> findDistinctCategories();

    void deleteByCategoryAndPredictedDemandIsNotNull(String category);
}
