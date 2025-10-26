{
  "displayName": "Uptime Check Failed (>=2 checker locations) - ${CHECK_NAME} (${HOST})",
  "userLabels": {
    "service": "${SERVICE_NAME}",
    "env": "prod"
  },
  "conditions": [
    {
      "displayName": "Uptime check failing in >=2 locations for ${WINDOW_MIN}m",
      "conditionMonitoringQueryLanguage": {
        "query": "fetch uptime_url | metric 'monitoring.googleapis.com/uptime_check/check_passed' | filter (resource.host == '${HOST}') && (metric.check_id == '${CHECK_ID}') | align next_older(${ALIGNMENT_SEC}s) | group_by [metric.checker_location], max(val()) | map val: 1 - val() | reduce sum(val) | condition val() >= 2",
        "duration": "${WINDOW_MIN}m"
      }
    }
  ],
  "documentation": {
    "content": "MQL alert: Uptime Check '${CHECK_NAME}' za host ${HOST} pada v vsaj 2 checker lokacijah v zadnjih ${WINDOW_MIN} minutah. Koraki: 1) Ročni curl test do ${SERVICE_URL}/health, 2) Uptime Checks -> preveri checker_location, 3) Cloud Run Logs (5xx/timeouts), 4) Deploy/revizije pred incidentom, 5) Odvisnosti (DB/API/kvote/DNS/TLS).",
    "mimeType": "text/markdown"
  },
  "alertStrategy": {
    "notificationRateLimit": { "period": "30m" },
    "autoClose": "30m"
  },
  "combiner": "OR",
  "enabled": true,
  "notificationChannels": [ ${NOTIFICATION_CHANNELS} ]
}