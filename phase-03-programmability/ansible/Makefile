.PHONY: deploy destroy bootstrap network srlinux hosts all validate clean

LAB_TOPOLOGY := ../topology/topology.clab.yml

deploy:
	sudo containerlab deploy -t $(LAB_TOPOLOGY)

destroy:
	sudo containerlab destroy -t $(LAB_TOPOLOGY)

inspect:
	sudo containerlab inspect -t $(LAB_TOPOLOGY)

bootstrap:
	./bootstrap.sh

network:
	ansible-playbook network.yml

srlinux:
	ansible-playbook srlinux.yml

hosts:
	ansible-playbook hosts.yml

validate:
	ansible-playbook network.yml --tags validate

all: bootstrap network srlinux hosts
	@echo "Full deployment complete."

clean: destroy
	@echo "Lab destroyed."

redeploy: destroy deploy all
	@echo "Full redeploy complete."
