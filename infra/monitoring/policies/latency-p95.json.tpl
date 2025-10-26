{
  "displayName": "Cloud Run P95 Latency - ${SERVICE_NAME}",
  "userLabels": {
    "service": "${SERVICE_NAME}",
    "env": "prod"
  },
  "conditions": [
    {
      "displayName": "P95 latency > ${P95_MS} ms for ${WINDOW_MIN}m",
      "conditionThreshold": {
        "filter": "resource.type=\"cloud_run_revision\" AND resource.label.\"service_name\"=\"${SERVICE_NAME}\" AND metric.type=\"run.googleapis.com/request_latencies\"",
        "aggregations": [
          {
            "alignmentPeriod": "${ALIGNMENT_SEC}s",
            "perSeriesAligner": "ALIGN_PERCENTILE_95",
            "crossSeriesReducer": "REDUCE_MAX",
            "groupByFields": [
              "resource.label.\"service_name\""
            ]
          }
        ],
        "comparison": "COMPARISON_GT",
        "thresholdValue": ${P95_MS},
        "duration": "${WINDOW_MIN}m",
        "trigger": {
          "count": 1
        }
      }
    }
  ],
  "combiner": "OR",
  "enabled": true,
  "notificationChannels": [ ${NOTIFICATION_CHANNELS} ]
}