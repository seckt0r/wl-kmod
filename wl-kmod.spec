# Define the kmod package name here.
%define kmod_name wl

# If kversion isn't defined on the rpmbuild line, define it here as the currently running kernel.
%{!?kversion: %define kversion $(uname -r)}

Name:    %{kmod_name}-kmod
Version: 6_30_223_271
Release: 3%{?dist}
Group:   System Environment/Kernel
License: Broadcom
Summary: %{kmod_name} kernel module(s)
URL:     http://www.broadcom.com/support/802.11/

BuildRequires: redhat-rpm-config, kernel-abi-whitelists, perl
ExclusiveArch: x86_64

# Sources.
#Source0:  hybrid-v35-nodebug-pcoem-%{version}.tar.gz
Source1:  hybrid-v35_64-nodebug-pcoem-%{version}.tar.gz
Source2:  README_6.30.223.271.txt
Source10: kmodtool-%{kmod_name}-el7.sh

# Ensure that the tarballs ARE NOT packaged.
#NoSource: 0
NoSource: 1

# Patches.
Patch0:     wl-kmod-001_wext_workaround.patch
Patch1:     wl-kmod-002_kernel_3.18_null_pointer.patch
Patch2:     wl-kmod-003_gcc_4.9_remove_TIME_DATE_macros.patch
Patch3:     wl-kmod-004_kernel_4.3_rdtscl_to_rdtsc.patch
Patch4:     wl-kmod-005_kernel_4.7_IEEE80211_BAND_to_NL80211_BAND.patch
Patch5:     wl-kmod-006_gcc_6_fix_indentation_warnings.patch
Patch6:     wl-kmod-007_kernel_4.8_add_cfg80211_scan_info_struct.patch
Patch7:     wl-kmod-008_fix_kernel_warnings.patch

# Magic hidden here.
%{expand:%(sh %{SOURCE10} rpmtemplate %{kmod_name} %{kversion} "")}

# Disable the building of the debug package(s).
%define debug_package %{nil}

%description
This package provides the Broadcom hybrid %{kmod_name} kernel module(s).
It is built to depend upon the specific ABI provided by a range of releases
of the same variant of the Linux kernel and not on any one specific build.

%prep
%setup -q -n %{kmod_name}-kmod-%{version} -c -T
#%ifarch i686
#%setup -q -D -T -a 0
#%endif
%ifarch x86_64
%setup -q -D -T -a 1
%endif
%patch0 -p1
%patch1 -p1
%patch2 -p1
%patch3 -p1
%patch4 -p1
%patch5 -p1
%patch6 -p1
%patch7 -p1

# Define kvl & kvr for use below in "patching" logicals
%define kvl %(echo %{kversion} | cut -d"-" -f1)
%define kvr %(echo %{kversion} | cut -d"-" -f2 | cut -d"." -f1)

# Perform "patching" edits to the src/wl/sys/wl_cfg80211_hybrid.c file.
#  Note: Using this method, as opposed to making a patch, allows 
#   the nosrc.rpm to be compiled under various point release kernels.
#  Note: Use [ >][>=] where both >= & > are present
%if "%{kvl}" == "4.9.11"
%if %{kvr} >= 123
#  Apply to EL 7.0 point release and later
#   >  No changes currently needed for EL 7.0 point release
%endif
%if %{kvr} >= 1
#  Apply to EL 7.3 point release and later
%{__sed} -i 's/ < KERNEL_VERSION(4,2,0)/ < KERNEL_VERSION(3, 9, 0)/' src/wl/sys/wl_cfg80211_hybrid.c
%{__sed} -i 's/ >= KERNEL_VERSION(4, 7, 0)/ >= KERNEL_VERSION(3, 10, 0)/' src/wl/sys/wl_cfg80211_hybrid.c
#
%endif
%if %{kvr} >= 229
#  Apply to EL 7.1 point release and later
%{__sed} -i 's/ >= KERNEL_VERSION(3, 11, 0)/ >= KERNEL_VERSION(3, 10, 0)/' src/wl/sys/wl_cfg80211_hybrid.c
%{__sed} -i 's/ >= KERNEL_VERSION(3, 15, 0)/ >= KERNEL_VERSION(3, 10, 0)/' src/wl/sys/wl_cfg80211_hybrid.c
%endif
%if %{kvr} >= 327
#  Apply to EL 7.2 point release and later
%{__sed} -i 's/ < KERNEL_VERSION(3, 18, 0)/ < KERNEL_VERSION(3, 9, 0)/' src/wl/sys/wl_cfg80211_hybrid.c
%{__sed} -i 's/ >= KERNEL_VERSION(4, 0, 0)/ >= KERNEL_VERSION(3, 10, 0)/' src/wl/sys/wl_cfg80211_hybrid.c
%endif
%if %{kvr} >= 514
#  Apply to EL 7.3 point release and later
%{__sed} -i 's/ < KERNEL_VERSION(4,2,0)/ < KERNEL_VERSION(3, 9, 0)/' src/wl/sys/wl_cfg80211_hybrid.c
%{__sed} -i 's/ >= KERNEL_VERSION(4, 7, 0)/ >= KERNEL_VERSION(3, 10, 0)/' src/wl/sys/wl_cfg80211_hybrid.c
#
%endif
%else
echo "This specification file has been written for use with RHEL 7 kernels only."
false
%endif

# Create the module override file.
echo "override %{kmod_name} * weak-updates/%{kmod_name}" > kmod-%{kmod_name}.conf

# Create the file to blacklist certain modules.
%{__cat} <<EOF > blacklist-Broadcom.conf
blacklist b43
blacklist b43legacy
blacklist bcm43xx
blacklist brcmsmac
blacklist ssb
blacklist bcma
EOF

# Create the file to modprobe the modules at system initialisation time.
%{__cat} <<EOF > kmod-%{kmod_name}.modules
#!/bin/bash

for M in lib80211 cfg80211 wl; do
    modprobe $M &>/dev/null
done
EOF

%build
if [ "%{apiwext}" == "1" ]
then
    %{__make} KBUILD_DIR=%{_usrsrc}/kernels/%{kversion} API=WEXT
else
    %{__make} KBUILD_DIR=%{_usrsrc}/kernels/%{kversion}
fi

%install
%{__install} -d %{buildroot}/lib/modules/%{kversion}/extra/%{kmod_name}/
%{__install} %{kmod_name}.ko %{buildroot}/lib/modules/%{kversion}/extra/%{kmod_name}/
%{__install} -d %{buildroot}%{_sysconfdir}/depmod.d/
%{__install} kmod-%{kmod_name}.conf %{buildroot}%{_sysconfdir}/depmod.d/
%{__install} -d %{buildroot}/usr/lib/modprobe.d/
%{__install} blacklist-Broadcom.conf %{buildroot}/usr/lib/modprobe.d/
%{__install} -d %{buildroot}%{_sysconfdir}/sysconfig/modules/
%{__install} kmod-%{kmod_name}.modules %{buildroot}%{_sysconfdir}/sysconfig/modules/
%{__install} -d %{buildroot}%{_defaultdocdir}/kmod-%{kmod_name}-%{version}/
%{__install} %{SOURCE2} %{buildroot}%{_defaultdocdir}/kmod-%{kmod_name}-%{version}/README.txt
%{__install} lib/LICENSE.txt %{buildroot}%{_defaultdocdir}/kmod-%{kmod_name}-%{version}/

# Strip the modules(s).
find %{buildroot} -type f -name \*.ko -exec %{__strip} --strip-debug \{\} \;

# Sign the modules(s).
%if %{?_with_modsign:1}%{!?_with_modsign:0}
# If the module signing keys are not defined, define them here.
%{!?privkey: %define privkey %{_sysconfdir}/pki/SECURE-BOOT-KEY.priv}
%{!?pubkey: %define pubkey %{_sysconfdir}/pki/SECURE-BOOT-KEY.der}
for module in $(find %{buildroot} -type f -name \*.ko);
do %{__perl} /usr/src/kernels/%{kversion}/scripts/sign-file \
    sha256 %{privkey} %{pubkey} $module;
done
%endif

%clean
%{__rm} -rf %{buildroot}

%changelog
* Wed Nov 9 2016 S.Tindall <s10dal@elrepo.org> - 6_30_223_271-3
- Added modified Fedora 23 RPMFusion NonFree wl-kmod-005_kernel_4.7_IEEE80211_BAND_to_NL80211_BAND.patch (from wl-kmod-6.30.223.271-7.fc23.src.rpm)
- Updated to build for EL 7.3

* Thu Nov 19 2015 S.Tindall <s10dal@elrepo.org> - 6_30_223_271-2
- Updated to build for EL 7.2

* Mon Oct 5 2015 S.Tindall <s10dal@elrepo.org> - 6_30_223_271-1
- Updated to use the 6_30_223_271 tarballs.

* Sat Mar 14 2015 Philip J Perry <phil@elrepo.org> - 6_30_223_248-3
- Update for RHEL7.1 [http://elrepo.org/bugs/view.php?id=559]

* Tue Jul 22 2014 The Doctor <DrWho@Gallifrey.Kasterborus> - 6_30_223_248-2
- Corrected the path to the /modprobe.d/ directory.

* Mon Jul 21 2014 The Doctor <DrWho@Gallifrey.Kasterborus> - 6_30_223_248-1
- Initial el7 build of the kmod package.
