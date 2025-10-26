# Quantum Package (Minimal)

Ta mapa vsebuje minimalni paket za zagon ključnih "quantum" storitev:
- quantum-platform (port 8080)
- quantum-api-gateway (port 8082)
- quantum-worker (port 8084)

## Zahteve
- Docker in Docker Compose
- Dostop do korena repozitorija (ta paket uporablja Dockerfile-e iz korena)

## Hiter zagon
```
cd quantum-package
# Po želji uredite .env
# Zgradite in zaženite storitve
docker compose -f docker-compose.quantum.min.yml up --build
```

## Zdravje storitev
- Platforma: http://localhost:8080/health
- API Gateway: http://localhost:8082/api/v1/health
- Worker: http://localhost:8084/worker/health

## Nastavitve (.env)
Spremenljivke v `.env` lahko prilagodite:
- `API_PORT=8082`
- `WORKER_ID=worker-1`
- `QUANTUM_PLATFORM_URL=http://quantum-platform:8080`
- `ENABLE_CORS=true`

## Ustavitev
```
docker compose -f docker-compose.quantum.min.yml down
```

## Opombe
- V Dockerfile-ih je vklopljeno univerzalno UTF-8 kodiranje (LANG/LC_ALL/PYTHONIOENCODING).
- Ta minimalni paket ne vključuje Redis, dashboard ali entanglement node.