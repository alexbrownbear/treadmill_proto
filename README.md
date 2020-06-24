### **Evofitness Cosmo 5 remote control**

##### Черновик

Сброс bluetooth устройства linux

```shell script
lsusb -tv
sudo usb_modeswitch -R -v <vendor ID> -p <product ID>
# acer spin 1 (intel 7062)
sudo usb_modeswitch -R -v 8087 -p 0a2a
```
Источник: [Adapter disappears after suspend/resume](https://wiki.archlinux.org/index.php/bluetooth#Adapter_disappears_after_suspend/resume)

Команды bluetooth управления linux
```shell script
# Список устройств
hcitool dev
# Скан
hcitool scan
hcitool lescan  # ble

# Блокировки уст-в
rfkill list

# Статус службы
systemctl status bluetooth

# Оборудование (intel)
lspci -nnk | grep 0280 -A3
```



[Adapter disappears after suspend/resume
]: https://wiki.archlinux.org/index.php/bluetooth#Adapter

[]: https://wiki.archlinux.org/index.php/bluetooth#Adapter