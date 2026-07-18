# Halo Blog Server — Cloudflare Tunnel Deployment Notes

This reference contains Halo-specific deployment details for use with Cloudflare Tunnel.

## Full docker-compose for Halo + Cloudflare Tunnel

```yaml
services:
  halo:
    image: registry.fit2cloud.com/halo/halo:2.24.2
    restart: always
    depends_on:
      halodb:
        condition: service_healthy
    networks:
      halo_network:
    volumes:
      - ./halo2:/root/.halo2
    ports:
      - "8090:8090"
    command:
      - --spring.r2dbc.url=r2dbc:pool:mysql://halodb:3306/halo
      - --spring.r2dbc.username=root
      - --spring.r2dbc.password=${DB_PASSWORD}
      - --spring.sql.init.platform=mysql
      - --halo.external-url=https://blog.yourdomain.com

  halodb:
    image: mysql:8.1.0
    restart: always
    networks:
      halo_network:
    environment:
      - MYSQL_ROOT_PASSWORD=${DB_PASSWORD}
      - MYSQL_DATABASE=halo

  cloudflared:
    image: cloudflare/cloudflared:latest
    restart: always
    networks:
      - halo_network
    command: tunnel --no-autoupdate run --token ${CF_TUNNEL_TOKEN}
    depends_on:
      halo:
        condition: service_healthy

networks:
  halo_network:
```

## Dashboard Hostname Config

```
Public hostname: blog.yourdomain.com
Service:         http://halo:8090
```

## Key Settings

- **external-url**: Must be set to the public HTTPS domain (`--halo.external-url=https://blog.yourdomain.com`) so Halo generates correct absolute URLs
- **Database**: MySQL must be healthy before Halo starts (depends_on with condition)
- **Network**: All three services share `halo_network` so cloudflared can reach `halo:8090`

## Troubleshooting Halo-Specific Issues

### Halo shows 502 via tunnel
1. Check `docker compose logs halo` — database connection issues are common
2. Verify `halodb` health check passes
3. Ensure `DB_PASSWORD` matches in both halo and halodb environment

### Mixed content warnings
- Halo generates absolute URLs from `external-url` setting
- If using Cloudflare Tunnel, ensure `external-url` uses `https://`
- Cloudflare terminates SSL, so no cert config needed in Halo itself

### Migration between servers
See main skill: Migration section for Halo export/import, MySQL dump/restore, and official migration tool.
