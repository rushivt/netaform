.PHONY: deploy destroy bootstrap network hosts all validate clean

LAB_TOPOLOGY := ../phase-01-branch-office/topology/topology.clab.yml

deploy:
	sudo containerlab deploy -t $(LAB_TOPOLOGY)

destroy:
	sudo containerlab destroy -t $(LAB_TOPOLOGY)

bootstrap:
	./bootstrap.sh

network:
	ansible-playbook network.yml

hosts:
	ansible-playbook hosts.yml

validate:
	ansible-playbook network.yml --tags validate

all: bootstrap network hosts
	@echo "Full deployment complete."

clean: destroy
	@echo "Lab destroyed."

redeploy: destroy deploy all
	@echo "Full redeploy complete."