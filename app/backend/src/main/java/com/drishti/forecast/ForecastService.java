package com.drishti.forecast;

import com.drishti.ml.InferenceClient;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class ForecastService {

    /** Module 4's longest lag feature; below this the model cannot build a row. */
    private static final int MIN_HISTORY_WEEKS = 52;

    private final ForecastPointRepository repository;
    private final InferenceClient inference;

    public ForecastService(ForecastPointRepository repository, InferenceClient inference) {
        this.repository = repository;
        this.inference = inference;
    }

    public List<String> categories() {
        return repository.findDistinctCategories();
    }

    public CategorySeries series(String category) {
        List<ForecastPoint> points = repository.findByCategoryOrderByWeekAsc(category);
        List<ForecastPoint> history = points.stream().filter(p -> p.getActualDemand() != null).toList();
        List<ForecastPoint> predicted = points.stream().filter(p -> p.getPredictedDemand() != null).toList();
        Double wape = points.stream().map(ForecastPoint::getWapePct).filter(w -> w != null).findFirst().orElse(null);
        return new CategorySeries(category, wape, history, predicted);
    }

    /**
     * Recomputes the forward forecast for a category and replaces its previous
     * predicted rows. Module 4's features include a 52-week lag, so when the
     * database holds fewer recorded weeks than that -- which it does for the
     * seeded 16-week series -- history is left null and the inference service
     * forecasts from the full recorded series on disk instead.
     */
    @Transactional
    public List<ForecastPoint> run(String category, int horizon) {
        List<ForecastPoint> history = repository.findByCategoryOrderByWeekAsc(category).stream()
                .filter(p -> p.getActualDemand() != null)
                .toList();

        List<Map<String, Object>> payload = null;
        if (history.size() >= MIN_HISTORY_WEEKS) {
            payload = new ArrayList<>();
            for (ForecastPoint p : history) {
                Map<String, Object> row = new HashMap<>();
                row.put("week", p.getWeek().toString());
                row.put("value", p.getActualDemand());
                payload.add(row);
            }
        }

        InferenceClient.ForecastResponse response = inference.forecast(category, payload, horizon);

        repository.deleteByCategoryAndPredictedDemandIsNotNull(category);

        List<ForecastPoint> saved = new ArrayList<>();
        for (InferenceClient.ForecastPointDto dto : response.forecast()) {
            ForecastPoint point = new ForecastPoint();
            point.setCategory(category);
            point.setWeek(LocalDate.parse(dto.week()));
            point.setPredictedDemand(dto.predicted_demand());
            point.setLowerP10(dto.lower());
            point.setUpperP90(dto.upper());
            saved.add(repository.save(point));
        }
        return saved;
    }

    public record CategorySeries(String category, Double wapePct,
                                 List<ForecastPoint> history, List<ForecastPoint> forecast) {}
}
