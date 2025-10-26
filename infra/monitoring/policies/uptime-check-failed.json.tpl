{
  "displayName": "Uptime Check Failed - ${CHECK_NAME} (${HOST})",
  "userLabels": {
    "service": "${SERVICE_NAME}",
    "env": "prod"
  },
  "conditions": [
    {
      "displayName": "Uptime check not passing for ${WINDOW_MIN}m",
      "conditionThreshold": {
        "filter": "resource.type=\"uptime_url\" AND metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\" AND resource.label.\"host\"=\"${HOST}\" AND metric.label.\"check_id\"=\"${CHECK_ID}\"",
        "aggregations": [
          {
            "alignmentPeriod": "${ALIGNMENT_SEC}s",
            "perSeriesAligner": "ALIGN_NEXT_OLDER",
            "crossSeriesReducer": "REDUCE_MAX",
            "groupByFields": [
              "resource.label.\"host\"",
              "metric.label.\"check_id\""
            ]
          }
        ],
        "comparison": "COMPARISON_LT",
        "thresholdValue": 1,
        "duration": "${WINDOW_MIN}m",
        "trigger": {
          "count": 1
        }
      }
    }
  ],
  "documentation": {
    "content": "Uptime Check is failing for ${CHECK_NAME} on host ${HOST}. Investigate service health, endpoint availability (/health), recent deployments, and upstream dependencies. This alert fires when 'check_passed' stays < 1 for the configured window.",
    "mimeType": "text/markdown"
  },
  "combiner": "OR",
  "enabled": true,
  "notificationChannels": [ ${NOTIFICATION_CHANNELS} ]
}