# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

  config.ssh.insert_key = false

  config.vm.define "umbra_virtualbox" do |umbra_virtualbox|

    umbra_virtualbox.vm.box = "ubuntu/focal64"    
    umbra_virtualbox.vm.network :private_network, ip: "192.168.56.10"
    umbra_virtualbox.vm.hostname = "umbra"
    
    umbra_virtualbox.vm.provider "virtualbox" do |vb|
      vb.name = "umbra"
      opts = ["modifyvm", :id, "--natdnshostresolver1", "on"]
      vb.customize opts
      vb.cpus = 2
      vb.memory = "2048"
    end

    umbra_virtualbox.vm.synced_folder ".", "/home/umbra", mount_options: ["dmode=775"]
    umbra_virtualbox.vm.provision :shell, inline: "apt update && apt install -y make"
    umbra_virtualbox.vm.provision :shell, inline: "cd /home/umbra && make install"

  end


  config.vm.define "umbra_libvirt" do |umbra_libvirt|
 
    umbra_libvirt.vm.box = "generic/ubuntu2004"
    umbra_libvirt.vm.hostname = "umbra"

    umbra_libvirt.vm.provider "libvirt" do |libvirt|
      libvirt.cpus = 2
      libvirt.memory = 2048
    end

    umbra_libvirt.vm.synced_folder ".", "/home/umbra", mount_options: ["dmode=775"]
    umbra_libvirt.vm.provision :shell, inline: "apt update && apt install -y make"
    umbra_libvirt.vm.provision :shell, inline: "cd /home/umbra && make install"

  end

end