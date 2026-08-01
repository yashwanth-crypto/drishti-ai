package com.drishti.forecast;

import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/forecast")
public class ForecastController {

    private final ForecastService service;

    public ForecastController(ForecastService service) {
        this.service = service;
    }

    @GetMapping("/categories")
    public List<ForecastService.CategorySeries> categories() {
        return service.categories().stream().map(service::series).toList();
    }

    @GetMapping("/categories/{category}")
    public ForecastService.CategorySeries category(@PathVariable String category) {
        return service.series(category);
    }

    @PostMapping("/run")
    public List<ForecastPoint> run(@RequestParam String category,
                                   @RequestParam(defaultValue = "4") int horizon) {
        return service.run(category, horizon);
    }
}
