# -*- mode: ruby -*-
# vi: set ft=ruby :
Vagrant.configure("2") do |config|
# Always use Vagrant's default insecure key	
  config.ssh.insert_key = false
  config.vbguest.auto_update = true
  config.vm.box_check_update = false  

  # create umbra node
  config.vm.define :umbra do |umbra_config|
	#Ubuntu 20.04, use ubuntu/groovy64 for Ubuntu 20.10
    umbra_config.vm.box = "ubuntu/focal64"
    umbra_config.vm.hostname = "umbra"
    umbra_config.vm.network :private_network, ip: "192.168.56.10"
    umbra_config.vm.synced_folder ".", "/home/umbra", mount_options: ["dmode=775"]
    umbra_config.vm.provider "virtualbox" do |vb|
      vb.name = "umbra-node"
      opts = ["modifyvm", :id, "--natdnshostresolver1", "on"]
      vb.customize opts
      vb.memory = "1024"
    end
    umbra_config.vm.provision :shell, path: "build/build.sh"
    umbra_config.vm.provision :shell, path: "build/build_fabric.sh"
  end
end
