# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

  config.ssh.insert_key = false

  config.vm.define "umbra_virtualbox" do |umbra_virtualbox|

    umbra_virtualbox.vm.box = "ubuntu/focal64"    
    umbra_virtualbox.vm.network :private_network, ip: "192.168.121.101"
    umbra_virtualbox.vm.hostname = "umbra-vm"
    
    umbra_virtualbox.vm.provider "virtualbox" do |vb|
      vb.name = "umbra"
      opts = ["modifyvm", :id, "--natdnshostresolver1", "on"]
      vb.customize opts
      vb.cpus = 4
      vb.memory = "4096"
    end

    umbra_virtualbox.vm.provision :shell, inline: "adduser umbra --gecos 'umbra hyperledger-labs,RoomNumber,WorkPhone,HomePhone' --disabled-password"
    umbra_virtualbox.vm.provision :shell, inline: "echo 'umbra:L1v3s.' | chpasswd"    
    umbra_virtualbox.vm.provision :shell, inline: "echo 'umbra  ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/umbra"

    umbra_virtualbox.vm.synced_folder ".", "/mnt/umbra", mount_options: ["dmode=775"]
    umbra_virtualbox.vm.provision :shell, inline: "apt update && apt install -y make net-tools"
    umbra_virtualbox.vm.provision :shell, inline: "cd /mnt/umbra && make install"

  end


  config.vm.define "umbra_libvirt" do |umbra_libvirt|
 
    umbra_libvirt.vm.box = "generic/ubuntu2004"
    umbra_libvirt.vm.hostname = "umbra-vm"
    umbra_libvirt.vm.network :private_network, ip: "192.168.121.101"

    umbra_libvirt.vm.provider "libvirt" do |libvirt|
      libvirt.cpus = 4
      libvirt.memory = 4096
    end
    umbra_libvirt.vm.provision :shell, inline: "adduser umbra --gecos 'umbra hyperledger-labs,RoomNumber,WorkPhone,HomePhone' --disabled-password"
    umbra_libvirt.vm.provision :shell, inline: "echo 'umbra:L1v3s.' | chpasswd"    
    umbra_libvirt.vm.provision :shell, inline: "echo 'umbra  ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/umbra"

    umbra_libvirt.vm.synced_folder ".", "/mnt/umbra", mount_options: ["dmode=775"]
    umbra_libvirt.vm.provision :shell, inline: "apt update && apt install -y make net-tools"
    umbra_libvirt.vm.provision :shell, inline: "cd /mnt/umbra && make install"

  end

end