.PHONY: deploy destroy bootstrap network hosts all validate clean redeploy test

LAB_TOPOLOGY := ../topology/topology.clab.yml

deploy:
	sudo containerlab deploy -t $(LAB_TOPOLOGY)

destroy:
	sudo containerlab destroy -t $(LAB_TOPOLOGY) || true

bootstrap:
	chmod +x bootstrap.sh
	./bootstrap.sh

network:
	ansible-playbook network.yml

hosts:
	ansible-playbook hosts.yml

validate:
	ansible-playbook network.yml --tags validate

test:
	cd ../scripts && python3 -m pytest tests/ -v --tb=short

all: bootstrap network hosts
	@echo ""
	@echo "=== Full deployment complete ==="

clean: destroy
	@echo "Lab destroyed."

redeploy: destroy deploy all
	@echo ""
	@echo "=== Full redeploy complete ==="
