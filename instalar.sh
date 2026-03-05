#!/bin/bash
echo "Instalando Peralt..."
sudo cp ~/peralt/peralt.py /usr/local/lib/peralt.py
echo '#!/bin/bash' | sudo tee /usr/local/bin/peralt
echo 'python3 /usr/local/lib/peralt.py "$@"' | sudo tee -a /usr/local/bin/peralt
sudo chmod +x /usr/local/bin/peralt
echo "✅ Peralt instalado! Ya podes usar: peralt archivo.peralt"
