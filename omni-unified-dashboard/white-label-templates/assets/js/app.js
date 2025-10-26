// Preprost JS za barvno temo iz konfiguracije znamke
fetch('../config/brand_config.json').then(r => r.json()).then(cfg => {
  document.documentElement.style.setProperty('--accent', cfg.primary_color || '#1e90ff');
});