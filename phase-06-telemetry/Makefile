.PHONY: deploy destroy redeploy status logs-gnmic logs-prometheus validate

# Deploy the full topology + telemetry stack
deploy:
	@echo "=== Deploying Netaform Phase 6 ==="
	cd topology && sudo clab deploy -t topology.clab.yml
	@echo ""
	@echo "=== Waiting for cEOS devices to boot ==="
	@for device in edge-1 dist-1 dist-2; do \
		echo -n "  Waiting for $$device..."; \
		until docker exec clab-netaform-p6-$$device Cli -c "show version" > /dev/null 2>&1; do \
			sleep 5; \
		done; \
		echo " ready"; \
	done
	@echo ""
	@echo "=== Deployment complete ==="
	@echo "  Grafana:    http://localhost:3000  (admin/admin)"
	@echo "  Prometheus: http://localhost:9090"
	@echo "  gnmic metrics: http://localhost:9804/metrics"

# Destroy the topology
destroy:
	cd topology && sudo clab destroy -t topology.clab.yml --cleanup

# Destroy and redeploy
redeploy: destroy deploy

# Check container status
status:
	docker ps --filter "label=clab-topo-file" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# View gnmic logs (useful for debugging subscriptions)
logs-gnmic:
	docker logs clab-netaform-p6-gnmic --tail 50 -f

# View prometheus logs
logs-prometheus:
	docker logs clab-netaform-p6-prometheus --tail 50 -f

# Quick validation - check all services are reachable
validate:
	@echo "=== Validating telemetry stack ==="
	@echo -n "  gnmic exporter... "
	@docker exec clab-netaform-p6-gnmic wget -qO /dev/null http://localhost:9804/metrics 2>&1 && echo "OK" || echo "FAIL"
	@echo -n "  Prometheus... "
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:9090/-/ready | grep -q 200 && echo "OK" || echo "FAIL"
	@echo -n "  Grafana... "
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/api/health | grep -q 200 && echo "OK" || echo "FAIL"
	@echo ""
	@echo "=== Checking gNMI on cEOS devices ==="
	@for device in edge-1 dist-1 dist-2; do \
		echo -n "  $$device gNMI... "; \
		docker exec clab-netaform-p6-$$device Cli -c "show management api gnmi" 2>/dev/null | grep -q "Enabled" && echo "OK" || echo "FAIL"; \
	done
