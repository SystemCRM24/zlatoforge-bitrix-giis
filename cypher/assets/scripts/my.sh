#!/bin/bash

#
# Установка сертификатов пользователя для проверки и подписания
#
#cd "/certs/scripts/"
# cd "$(dirname "$0")"


source ./lib/colors.sh
source ./lib/functions.sh

dir=$(mktemp -d)
cd "$dir"
cat - > "bundle.zip"
unzip -q bundle.zip
rm bundle.zip

# проверка всех необходимых файлов в закрытом ключе
function testprivk {
  [ ! -f "$contShortName/header.key" ] && error "File header.key not found in $contShortName" && exit 1
  [ ! -f "$contShortName/masks.key" ] && error "File masks.key not found in $contShortName" && exit 1
  [ ! -f "$contShortName/masks2.key" ] && error "File masks2.key not found in $contShortName" && exit 1
  [ ! -f "$contShortName/name.key" ] && error "File name.key not found in $contShortName" && exit 1
  [ ! -f "$contShortName/primary.key" ] && error "File primary.key not found in $contShortName" && exit 1
  [ ! -f "$contShortName/primary2.key" ] && error "File primary2.key not found in $contShortName" && exit 1
}

certFileName=$(find -maxdepth 1 -type f \! -name . | head -n1 | xargs -I{} basename {})
contShortName=$(find -maxdepth 1 -type d \! -name . | head -n1 | xargs -I{} basename {})

# Есть контейнер, устанавливаем
if [ -n "$contShortName" ]; then
  echo "Key container short name: $contShortName"
  testprivk

  # --- ГЛАВНОЕ ИСПРАВЛЕНИЕ: Создаем директорию, если она не существует ---
  mkdir -p /var/opt/cprocsp/keys/root

  cp -R "$contShortName" /var/opt/cprocsp/keys/root/
  
  # --- ВАЖНО: Устанавливаем правильные права доступа ---
  # chmod -R a+rX "/var/opt/cprocsp/keys/root/$contShortName"
  
  if [ "$?" -eq "0" ]; then
    echo "Key container installed"
  fi
fi

# Есть сертификат
if [ -n "$certFileName" ]; then
	if [ ! -n "$contShortName" ]; then
		# устанавливается только сертификат
		certmgr -inst -file "$certFileName"
		if [ "$?" -eq "0" ]; then
			echo "Certificate installed"
			echo "No PrivateKey Link"
		fi
	else
		# устанавливается сертификат + контейнер
		echo "Trying to find full container name for: $contShortName"
		contFullName=$(/opt/cprocsp/bin/amd64/csptest -keyset -enum_cont -fqcn | grep -F "$contShortName" | cut -d'|' -f 1)

		if [ -z "$contFullName" ]; then
			echo "Could not find installed container with short name: $contShortName"
			rm -rf "$dir"
			exit 1
		fi
		
		echo "Key container full name: $contFullName"

		if [ -z "$1" ]; then
			certmgr -inst -file "$certFileName" -cont "$contFullName"
	    else
			certmgr -inst -file "$certFileName" -pin "$1" -cont "$contFullName"
	    fi

		if [ "$?" -eq "0" ]; then
			echo "Certificate installed with PrivateKey Link"
		fi
	fi
fi

rm -rf "$dir"