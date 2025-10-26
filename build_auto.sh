#!/bin/bash

# Bash verzija (build_auto.sh)
# Aktiviraj virtualno okolje
VENV_PATH="./OMNIBOT13/.venv/bin/activate"

if [ -f "$VENV_PATH" ]; then
    echo -e "\033[1;32m✅ Aktiviram virtualno okolje...\033[0m"
    source "$VENV_PATH"
    echo -e "\033[1;32m✅ Virtualno okolje aktivirano\033[0m"
else
    echo -e "\033[1;31m❌ Virtualno okolje ne najdem na $VENV_PATH\033[0m"
    echo -e "\033[1;33m⚠️ Nadaljujem brez aktivacije...\033[0m"
fi

STATE_FILE="./omni_build_state.json"

# Če datoteka ne obstaja, jo ustvari
if [ ! -f "$STATE_FILE" ]; then
    echo -e "\033[1;33m📄 Stanje gradnje ne obstaja, ustvarjam novo...\033[0m"

    cat > "$STATE_FILE" << 'EOL'
{
  "modules": [],
  "last_updated": null
}
EOL

    echo -e "\033[1;32m✅ Novo stanje gradnje ustvarjeno\033[0m"
fi

# Funkcija za gradnjo modula
build_module() {
    local module=$1
    local start_time=$(date +%s)

    echo -e "\033[1;36m🔨 Gradim modul: $module\033[0m"
    echo -e "\033[1;36m────────────────────────────────────────\033[0m"

    # Preveri če je modul že zgrajen
    local existing_status=$(jq -r --arg name "$module" '.modules[] | select(.name==$name) | .status' "$STATE_FILE" 2>/dev/null || echo "not_found")

    if [ "$existing_status" = "built" ]; then
        local last_build=$(jq -r --arg name "$module" '.modules[] | select(.name==$name) | .last_build' "$STATE_FILE" 2>/dev/null || echo "unknown")
        echo -e "\033[1;34m⏭️ Modul $module že zgrajen (nazadnje: $last_build), preskočim...\033[0m"
        return 0
    fi

    echo -e "\033[1;33m🏗️ Začenjam gradnjo modula $module...\033[0m"

    # Izvedi gradnjo
    if python build_module.py --module "$module"; then
        local end_time=$(date +%s)
        local build_duration=$((end_time - start_time))

        echo -e "\033[1;32m✅ Modul $module zgrajen uspešno!\033[0m"
        echo -e "\033[1;32m⏱️ Čas gradnje: ${build_duration}s\033[0m"

        # Posodobi stanje
        jq --arg name "$module" \
           --arg status "built" \
           --arg timestamp "$(date -Iseconds)" \
           --arg duration "$build_duration" \
           '.modules += [{"name":$name,"status":$status,"last_build":$timestamp,"build_time_seconds":($duration|tonumber)}] | .last_updated = $timestamp' \
           "$STATE_FILE" > tmp.$$.json && mv tmp.$$.json "$STATE_FILE"

        return 0
    else
        local end_time=$(date +%s)
        local build_duration=$((end_time - start_time))

        echo -e "\033[1;31m❌ Modul $module ni bil zgrajen!\033[0m"
        echo -e "\033[1;31m⏱️ Čas poskusa: ${build_duration}s\033[0m"

        # Posodobi stanje z napako
        jq --arg name "$module" \
           --arg status "failed" \
           --arg timestamp "$(date -Iseconds)" \
           --arg duration "$build_duration" \
           '.modules += [{"name":$name,"status":$status,"last_build":$timestamp,"build_time_seconds":($duration|tonumber)}] | .last_updated = $timestamp' \
           "$STATE_FILE" > tmp.$$.json && mv tmp.$$.json "$STATE_FILE"

        return 1
    fi
}

# Funkcija za prikaz statusa modula
show_module_status() {
    local module=$1
    local status=$(jq -r --arg name "$module" '.modules[] | select(.name==$name) | .status' "$STATE_FILE" 2>/dev/null || echo "not_found")
    local last_build=$(jq -r --arg name "$module" '.modules[] | select(.name==$name) | .last_build' "$STATE_FILE" 2>/dev/null || echo "unknown")

    case $status in
        "built")
            echo -e "  ✅ $module - Zgrajen ($last_build)"
            ;;
        "failed")
            echo -e "  ❌ $module - Spodletel ($last_build)"
            ;;
        "error")
            echo -e "  💥 $module - Napaka ($last_build)"
            ;;
        *)
            echo -e "  ⏳ $module - Ni zgrajen"
            ;;
    esac
}

# Vsi razpoložljivi moduli
all_modules=("omni-platform-v1.0.0" "omni-desktop-v1.0.0" "omni-frontend-v1.0.0")

echo -e "\033[1;35m🚀 OMNI Advanced Build System - Automated Build Script\033[0m"
echo -e "\033[1;35m════════════════════════════════════════════════════════════\033[0m"

echo -e "\033[1;37m📋 Razpoložljivi moduli za gradnjo:\033[0m"
for i in "${!all_modules[@]}"; do
    mod="${all_modules[$i]}"
    show_module_status "$mod"
done

# Poišči module, ki še niso zgrajeni ali so spodleteli
modules_to_build=()
for mod in "${all_modules[@]}"; do
    local status=$(jq -r --arg name "$mod" '.modules[] | select(.name==$name) | .status' "$STATE_FILE" 2>/dev/null || echo "not_found")

    if [ "$status" != "built" ]; then
        modules_to_build+=("$mod")
    fi
done

if [ ${#modules_to_build[@]} -eq 0 ]; then
    echo -e "\n\033[1;32m🎉 Vsi moduli so že zgrajeni!\033[0m"
    echo -e "\033[1;37mNaslednji koraki:\033[0m"
    echo -e "1. Test platforme: python omni_build_runner.py"
    echo -e "2. Zaženi desktop app: ./deployment-packages/omni-desktop-v1.0.0/OMNI\ AI\ Dashboard"
    echo -e "3. Preveri status: python omni_build_monitor.py"
    echo -e "4. Napredna analitika: python omni_real_time_build_analytics.py"
    exit 0
fi

echo -e "\n\033[1;35m🚀 Začenjam gradnjo modulov...\033[0m"
echo -e "\033[1;35m════════════════════════════════════════════════════════════\033[0m"

successful_builds=0
failed_builds=0
total_build_time=0

# Gradnja vseh neizgrajenih modulov
for module in "${modules_to_build[@]}"; do
    echo ""
    if build_module "$module"; then
        ((successful_builds++))
    else
        ((failed_builds++))
    fi
done

# Končno poročilo
echo -e "\n\033[1;36m📊 KONČNO POROČILO GRADNJE\033[0m"
echo -e "\033[1;36m════════════════════════════════════════════════════════════\033[0m"
echo -e "\033[1;32m✅ Uspešno zgrajenih modulov: $successful_builds\033[0m"
echo -e "\033[1;31m❌ Spodletelih modulov: $failed_builds\033[0m"
echo -e "\033[1;37m📈 Uspešnost: $(echo "scale=1; $successful_builds / ${#all_modules[@]} * 100" | bc -l)%\033[0m"

if [ $failed_builds -eq 0 ]; then
    echo -e "\n\033[1;32m🎉 VSE GRADNJE USPŠEŠNE! 🎉\033[0m"
    echo -e "\n\033[1;36mNaslednji koraki:\033[0m"
    echo -e "1. Test platforme: python omni_build_runner.py"
    echo -e "2. Zaženi desktop app: ./deployment-packages/omni-desktop-v1.0.0/OMNI\ AI\ Dashboard"
    echo -e "3. Preveri status: python omni_build_monitor.py"
    echo -e "4. Napredna analitika: python omni_real_time_build_analytics.py"
    echo -e "5. Kvantska optimizacija: python omni_quantum_optimizer.py"
    echo -e "6. Samozdravljenje: python omni_self_healing_build_system.py"
else
    echo -e "\n\033[1;33m⚠️ Nekatere gradnje so spodletle. Preveri napake zgoraj.\033[0m"
    echo -e "\n\033[1;36mZa pomoč:\033[0m"
    echo -e "1. Preveri detajle napak"
    echo -e "2. Poskusi ročno gradnjo: python build_module.py --module <module_name>"
    echo -e "3. Aktiviraj samozdravljenje: python omni_self_healing_build_system.py"
    echo -e "4. Preveri analitiko: python omni_real_time_build_analytics.py"
fi

echo -e "\n\033[1;34m💾 Stanje gradnje shranjeno v: $STATE_FILE\033[0m"
echo -e "\033[1;34m🔄 Za nadaljevanje gradnje samo poženite ta skript ponovno\033[0m"

# Posodobi končno stanje
jq --arg timestamp "$(date -Iseconds)" '.last_updated = $timestamp' "$STATE_FILE" > tmp.$$.json && mv tmp.$$.json "$STATE_FILE"

echo -e "\n\033[1;32m✅ Avtomatizirana gradnja dokončana!\033[0m"