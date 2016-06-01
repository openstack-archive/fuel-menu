%define name fuelmenu
%{!?version: %define version 10.0.0}
%{!?release: %define release 1}

Name: %{name}
Summary: Console utility for pre-configuration of Fuel server
Version: %{version}
Release: %{release}
Source0: %{name}-%{version}.tar.gz
License: Apache
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: Matthew Mosesohn <mmosesohn@mirantis.com>
BuildRequires:  python-setuptools
Requires: bind-utils
Requires: fuel-release
Requires: network-checker
Requires: ntp
Requires: python-requests >= 1.2.3
Requires: python-setuptools
Requires: python-netaddr
Requires: python-netifaces
Requires: python-urwid >= 1.1.0
Requires: PyYAML
Requires: screen
Requires: python-six
Requires: python-fuelclient
%if 0%{?rhel} == 6
Requires: python-ordereddict
%endif

%description
Summary: Console utility for pre-configuration of Fuel server

%prep
%setup -cq -n %{name}-%{version}

%build
cd %{_builddir}/%{name}-%{version} && python setup.py build

%install
cd %{_builddir}/%{name}-%{version} && python setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=%{_builddir}/%{name}-%{version}/INSTALLED_FILES
install -d -m 755 %{buildroot}/etc/fuel

%clean
rm -rf $RPM_BUILD_ROOT

%files -f %{_builddir}/%{name}-%{version}/INSTALLED_FILES
%defattr(-,root,root)
%dir /etc/fuel
