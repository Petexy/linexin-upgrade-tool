# Maintainer: Petexy <https://github.com/Petexy>

pkgname=linexin-upgrade-tool
pkgver=1.0.0.r
pkgrel=1
_currentdate=$(date +"%Y-%m-%d%H-%M-%S")
pkgdesc='Linexin Operating System Upgrader'
url='https://github.com/Petexy'
arch=(x86_64)
license=('GPL-3.0')
depends=(
  python-gobject
  gtk4
  libadwaita
  python
  linexin-center
)
makedepends=(
)

package() {
   mkdir -p ${pkgdir}/usr/share/linexin-upgrade-tool
   cp -rf ${srcdir}/usr ${pkgdir}/
}
