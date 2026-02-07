#!/bin/bash
echo "🚀 Starting Farm Allocation Protocol (HYPER VOLUME MODE) - INFINITE LOOP..."

# Function to run a farmer in a loop
run_farmer() {
    local symbol=$1
    local direction=$2
    local capital=$3
    local log_file=$4
    
    while true; do
        echo "🔄 Restarting $symbol Farm ($direction)..."
        # Flags: --mode surf --hyper-volume --mandatory-sl
        if [ "$direction" == "long" ]; then
            dir_flag="--long"
        else
            dir_flag="--short"
        fi
        
        # Reset orders only on first run? No, safe to reset on restart to clear stale orders.
        python3 obiwork_core/tools/volume_farmer.py \
            --symbols $symbol \
            --leverage 5 \
            --mode surf \
            $dir_flag \
            --capital-per-trade $capital \
            --obi 0.15 \
            --mandatory-sl \
            --hyper-volume \
            --reset-orders \
            >> $log_file 2>&1
            
        echo "⚠️ $symbol Farm crashed. Sleeping 5s before restart..."
        sleep 5
    done
}

# Kill previous instances
pkill -f volume_farmer
sleep 2

# 1. BTC_USDC_PERP (70% Allocation - Anchor)
# Direction: LONG (OBI +0.97) -> Use --long
# Capital: $168
run_farmer "BTC_USDC_PERP" "long" 168 "farm_btc.log" &

# 2. SKR_USDC_PERP (20% Allocation - Growth)
# Direction: LONG (OBI +0.80) -> Use --long
# Capital: $48
run_farmer "SKR_USDC_PERP" "long" 48 "farm_skr.log" &

# 3. FOGO_USDC_PERP (10% Allocation - Hedge/Speculation)
# Direction: SHORT (OBI -0.52) -> Use --short
# Capital: $24
run_farmer "FOGO_USDC_PERP" "short" 24 "farm_fogo.log" &

echo "✅ All farms started in INFINITE LOOP."
wait # Wait for background processes
