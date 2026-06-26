import React from "react";
import { ComparisonReport } from "@/services/upload";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "./ui/card";
import { AlertCircle, CheckCircle2, TrendingUp, Thermometer, Database } from "lucide-react";

export function ComparisonResultCard({ report }: { report: ComparisonReport }) {
  if (!report.is_valid) {
    return (
      <Card className="border-destructive/50 bg-destructive/5 shadow-sm my-2 max-w-2xl w-full">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-bold flex items-center gap-2 text-destructive">
            <AlertCircle className="h-4 w-4" />
            Validation Failed
          </CardTitle>
        </CardHeader>
        <CardContent className="text-sm">
          <ul className="list-disc pl-5 space-y-1 text-destructive/90">
            {report.warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </CardContent>
      </Card>
    );
  }

  const { similar_reactions, optimal_conditions, temperature_profile } = report.comparisons;

  return (
    <Card className="border-border bg-card shadow-sm my-2 max-w-2xl w-full">
      <CardHeader className="pb-2 border-b border-border/50 bg-muted/30">
        <div className="flex justify-between items-start">
          <div>
            <CardTitle className="text-base font-bold flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              Experiment Parsed & Validated
            </CardTitle>
            <p className="text-xs text-muted-foreground mt-1 font-mono">ID: {report.experiment_id}</p>
          </div>
          <div className="bg-primary/10 text-primary text-xs font-semibold px-2 py-1 rounded">
            Confidence: {Math.round((report.confidence_score || 0) * 100)}%
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="p-4 space-y-4">
        {report.warnings && report.warnings.length > 0 && (
          <div className="bg-yellow-500/10 border border-yellow-500/20 text-yellow-600 dark:text-yellow-400 p-3 rounded-md text-xs">
            <div className="font-semibold mb-1 flex items-center gap-1">
              <AlertCircle className="h-3 w-3" /> Warnings
            </div>
            <ul className="list-disc pl-4 space-y-0.5">
              {report.warnings.map((w, i) => <li key={i}>{w}</li>)}
            </ul>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {similar_reactions && (
            <div className="border border-border rounded-md p-3">
              <h4 className="text-xs font-bold text-muted-foreground uppercase flex items-center gap-1.5 mb-2">
                <Database className="h-3 w-3" /> Similar Reactions
              </h4>
              <div className="text-2xl font-bold">{similar_reactions.total_matching}</div>
              <p className="text-xs text-muted-foreground mt-1">matches found in database</p>
              {similar_reactions.top_matches.length > 0 && (
                <div className="mt-2 text-xs">
                  <span className="font-semibold">Top match:</span> {similar_reactions.top_matches[0].reaction_type || similar_reactions.top_matches[0].reaction_id}
                </div>
              )}
            </div>
          )}

          {optimal_conditions && (
            <div className="border border-border rounded-md p-3">
              <h4 className="text-xs font-bold text-muted-foreground uppercase flex items-center gap-1.5 mb-2">
                <TrendingUp className="h-3 w-3" /> Yield Analysis
              </h4>
              <div className="flex justify-between items-end">
                <div>
                  <div className="text-sm font-semibold">User: {optimal_conditions.user_yield ?? "--"}%</div>
                  <div className="text-sm font-semibold">Optimal: {optimal_conditions.best_avg_yield ? optimal_conditions.best_avg_yield.toFixed(1) : "--"}%</div>
                </div>
                {optimal_conditions.yield_classification && (
                  <span className={`text-xs px-2 py-0.5 rounded ${
                    optimal_conditions.yield_classification === "Excellent Match" || optimal_conditions.yield_classification === "Comparable"
                      ? "bg-green-500/20 text-green-700 dark:text-green-400"
                      : optimal_conditions.yield_classification === "Slightly Below Optimal"
                      ? "bg-yellow-500/20 text-yellow-700 dark:text-yellow-400"
                      : "bg-destructive/20 text-destructive dark:text-destructive"
                  }`}>
                    {optimal_conditions.yield_classification}
                  </span>
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-2 truncate">
                Best catalyst: {optimal_conditions.best_catalyst}
              </p>
            </div>
          )}

          {temperature_profile && (
            <div className="border border-border rounded-md p-3 md:col-span-2">
              <h4 className="text-xs font-bold text-muted-foreground uppercase flex items-center gap-1.5 mb-2">
                <Thermometer className="h-3 w-3" /> Temperature Profile
              </h4>
              <div className="flex justify-between items-center">
                <div className="text-sm">
                  User: <span className="font-semibold">{temperature_profile.user_temperature}°C</span>
                </div>
                <div className="text-sm">
                  DB Avg: <span className="font-semibold">{temperature_profile.db_average_temperature}°C</span>
                </div>
                <div className="text-sm">
                  Δ: <span className={`font-semibold ${temperature_profile.is_anomalous ? "text-destructive" : ""}`}>{temperature_profile.difference > 0 ? "+" : ""}{temperature_profile.difference}°C</span>
                </div>
                {temperature_profile.is_anomalous && (
                  <span className="text-xs bg-destructive/10 text-destructive px-2 py-0.5 rounded flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" /> Anomalous
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
