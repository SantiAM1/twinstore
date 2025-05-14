DOMAIN=twinstore.com.ar
EMAIL=contacto@twinstore.com.ar

# Generar certificados SSL (requiere Nginx corriendo con config temporal)
cert:
	docker compose up -d nginx
	docker compose run --rm certbot

# Renovar certificados SSL y recargar Nginx
renew:
	docker compose run --rm certbot renew
	docker compose exec nginx nginx -s reload

# Reiniciar todo el entorno (útil tras cambios de config)
restart:
	docker compose down
	docker compose up -d --build

# Ver logs de Nginx
logs-nginx:
	docker compose logs -f nginx

# Verificar estado de certificados
check:
	docker compose run --rm certbot certificates