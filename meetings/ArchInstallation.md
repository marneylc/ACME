# Arch Installation

Connect to wifi

```bash
wifi-menu
```

or try

```bash
nmcli
```

Partition drive 

```bash
lsblk
cfdisk /dev/sda
```

Create three partitions, 512MB for uefi boot, 100G for /, and rest for /home

Then format partitions

```bash
mkfs.fat -F32 /dev/sda1
mkfs.ext4 /dev/sda2
mkfs.ext4 /dev/sda3
```

Next, mount the root partition:

```bash
mount /dev/sda2 /mnt
```

Create a folder to mount the home partition and mount it:

```bash
mkdir /mnt/home
mount /dev/sda3 /mnt/home
```

Check mounting points whether they were created successfully with lsblk 

Then install the base system with pacstrap

```bash
pacstrap -i /mnt base base-devel linux linux-firmware sudo vi vim
```

Generate fstab 

```bash
genfstab -U -p /mnt >> /mnt/etc/fstab
```

Chroot to system

```bash
arch-chroot /mnt /bin/bash
```

Edit locale by un-commenting #en_US.UTF-8 UTF-8

```bash
vim /etc/locale.gen
```

Generate locale and create locale.conf

```bash
locale-gen
echo "LANG=en_US.UTF-8" > /etc/locale.conf
```

Set time zone

```bash
ln -sf /usr/share/zoneinfo/America/Vancouver /etc/localtime
```

Set local time

```bash
hwclock --systohc --utc
```

Set hostname

```bash
echo archlab > /etc/hostname
```

Edit /etc/hosts to include this line

```bash
127.0.1.1 localhost.localdomain archlab
```

Install network tools for laptop

```bash
pacman -S networkmanager iw iwd
```

Set root password

```bash
passwd
```

Install grub

```bash
pacman -S grub efibootmgr
```

Install the bootloader

```bash
mkdir /boot/efi
mount /dev/sda1 /boot/efi
lsblk # to check if everything is mounted correctly
grub-install --target=x86_64-efi --bootloader-id=GRUB --efi-directory=/boot/efi --removable
grub-mkconfig -o /boot/grub/grub.cfg
```

Unmount /mnt with -R, reboot into system and connect to wifi

Make non-root user

```bash
useradd -m -g users salamander
passwd salamander
```

Give sudo with visudo

---

Install stuff for window manager awesome

```bash
sudo pacman -S lightdm lightdm-gtk-greeter awesome xorg-server xterm termite ttf-dejavu git
```

Configure lightdm

```
sudo vim /etc/lightdm/lightdm.conf
```

---

---

i3 installation

when prompted select i3-gaps, i3blocks, i3lock, and i3status

```bash
pacman -S xorg-server xorg-apps xorg-xinit i3 dmenu
cp /etc/X11/xinit/xinitrc ~/.xinitrc
```

then edit .xinitrc to have

```bash
exec i3
```

install yay and brave

```bash
git clone https://aur.archlinux.org/yay.git
cd yay
makepkg -si
yay -S brave-bin
```

### For Autologin

In the section labeled `[Seat:*]` find the following lines.

```
# autologin-user=
# autologin-session=
```

Uncomment and add the correct argument like so.

```
autologin-user=<username>
autologin-session=awesome
```

LightDM requires an `autologin` group be set up and that your user be added to it in order to enable automatic login.

```
sudo groupadd -r autologin
sudo gpasswd -a lhennessy autologin
```

### For User Login

Edit /etc/lightdm/lightdm.conf

```jsx
greeter-session=lightdm-gtk-greeter
user-session=awesome
```

Enable the LightDM service by running the following as a user, not `root`

```
systemctl enable lightdm.service
```

Configure awesome

```bash
git clone --recursive https://github.com/lcpz/awesome-copycats.git
mv -bv awesome-copycats/* ~/.config/awesome && rm -rf awesome-copycats
```

in `theme.lua`, we just need to change `chosen_theme` variable in `rc.lua` to preserve preferences *and* switch the theme, instead of having file redundancy. I like powerarrow.

Just do the following:

```jsx
cd ~/.config/awesome
cp rc.lua.template rc.lua
```

Then, set the variable `chosen_theme` in `rc.lua` to your preferred theme, do your settings, and reboot or restart Awesome (`Mod4 + ctrl + r`).

To customize a theme, head over to `themes/$chosen_theme/theme.lua`
