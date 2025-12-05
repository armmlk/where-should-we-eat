import streamlit as st
import random
import json
import os
from pathlib import Path
import math
import time

# Configuration
DATA_FILE = "restaurants.json"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-me-now-12345")  # Set via environment variable

# Initialize session state
if 'spinning' not in st.session_state:
    st.session_state.spinning = False
if 'result' not in st.session_state:
    st.session_state.result = None
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'spin_angle' not in st.session_state:
    st.session_state.spin_angle = 0

def load_restaurants():
    """Load restaurants from JSON file"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_restaurants(restaurants):
    """Save restaurants to JSON file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(restaurants, f, indent=2)

def spin_wheel(restaurants):
    """Spin the wheel and select a restaurant based on probabilities"""
    if not restaurants:
        return None
    
    names = [r['name'] for r in restaurants]
    weights = [r['probability'] for r in restaurants]
    
    # Normalize weights
    total = sum(weights)
    if total == 0:
        weights = [1] * len(weights)
        total = len(weights)
    
    normalized_weights = [w / total for w in weights]
    
    return random.choices(names, weights=normalized_weights, k=1)[0]

def generate_wheel_svg(restaurants, rotation=0, highlight_index=None):
    """Generate an SVG representation of the spinning wheel"""
    if not restaurants:
        return "<svg></svg>"
    
    size = 400
    center = size / 2
    radius = 180
    
    # Calculate total probability
    total_prob = sum(r['probability'] for r in restaurants)
    
    # Colors for segments
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', 
              '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8B739', '#52C97F']
    
    svg = f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" style="transform: rotate({rotation}deg); transition: transform 0.1s linear;">'
    
    # Add circle border
    svg += f'<circle cx="{center}" cy="{center}" r="{radius}" fill="none" stroke="#333" stroke-width="4"/>'
    
    # Draw segments
    current_angle = 0
    for idx, restaurant in enumerate(restaurants):
        angle = (restaurant['probability'] / total_prob) * 360
        
        # Calculate arc path
        start_angle = math.radians(current_angle - 90)
        end_angle = math.radians(current_angle + angle - 90)
        
        x1 = center + radius * math.cos(start_angle)
        y1 = center + radius * math.sin(start_angle)
        x2 = center + radius * math.cos(end_angle)
        y2 = center + radius * math.sin(end_angle)
        
        large_arc = 1 if angle > 180 else 0
        
        color = colors[idx % len(colors)]
        if highlight_index == idx:
            color = '#FFD700'  # Gold for winner
        
        path = f'M {center} {center} L {x1} {y1} A {radius} {radius} 0 {large_arc} 1 {x2} {y2} Z'
        svg += f'<path d="{path}" fill="{color}" stroke="#fff" stroke-width="2"/>'
        
        # Add text label
        text_angle = math.radians(current_angle + angle/2 - 90)
        text_radius = radius * 0.7
        text_x = center + text_radius * math.cos(text_angle)
        text_y = center + text_radius * math.sin(text_angle)
        
        # Rotate text to be readable
        text_rotation = current_angle + angle/2
        name = restaurant['name']
        if len(name) > 15:
            name = name[:13] + '...'
        
        svg += f'<text x="{text_x}" y="{text_y}" font-size="14" font-weight="bold" text-anchor="middle" transform="rotate({text_rotation}, {text_x}, {text_y})" fill="#000">{name}</text>'
        
        current_angle += angle
    
    # Center circle
    svg += f'<circle cx="{center}" cy="{center}" r="30" fill="#333" stroke="#FFD700" stroke-width="3"/>'
    svg += f'<text x="{center}" y="{center + 5}" font-size="20" font-weight="bold" text-anchor="middle" fill="#FFD700">SPIN</text>'
    
    svg += '</svg>'
    
    # Add pointer at top
    pointer = f'<div style="position: relative; width: {size}px; margin: 0 auto;"><div style="position: absolute; top: -20px; left: 50%; transform: translateX(-50%); width: 0; height: 0; border-left: 15px solid transparent; border-right: 15px solid transparent; border-top: 30px solid #FF0000; z-index: 10;"></div>{svg}</div>'
    
    return pointer

# Main app
st.set_page_config(page_title="🍽️ Where Should We Eat?", page_icon="🎡", layout="wide")

st.title("🎡 Restaurant Fortune Wheel")
st.markdown("### Spin the wheel to decide where to eat!")

# Load restaurants
restaurants = load_restaurants()

# Main section - Spin the wheel
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    if restaurants:
        # Display the wheel
        wheel_placeholder = st.empty()
        
        if st.session_state.spinning:
            # Animate spinning
            final_result = st.session_state.result
            
            # Find winner index
            winner_idx = next((i for i, r in enumerate(restaurants) if r['name'] == final_result), 0)
            
            # Spin animation
            spins = 5  # Number of full rotations
            frames = 60
            for frame in range(frames):
                progress = frame / frames
                # Ease out effect
                eased_progress = 1 - math.pow(1 - progress, 3)
                
                rotation = eased_progress * (360 * spins + (360 * sum(r['probability'] for r in restaurants[:winner_idx+1]) / sum(r['probability'] for r in restaurants)))
                
                with wheel_placeholder.container():
                    st.markdown(generate_wheel_svg(restaurants, rotation), unsafe_allow_html=True)
                
                time.sleep(0.05)
            
            # Final position with highlight
            with wheel_placeholder.container():
                st.markdown(generate_wheel_svg(restaurants, rotation, winner_idx), unsafe_allow_html=True)
            
            st.session_state.spinning = False
            st.markdown("---")
            st.success(f"### 🎉 Let's eat at: **{final_result}**!")
            st.balloons()
            
        else:
            # Static wheel
            with wheel_placeholder.container():
                st.markdown(generate_wheel_svg(restaurants, 0), unsafe_allow_html=True)
        
        st.markdown("")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🎲 SPIN THE WHEEL!", type="primary", use_container_width=True, disabled=st.session_state.spinning):
                st.session_state.result = spin_wheel(restaurants)
                st.session_state.spinning = True
                st.rerun()
        
        with col_btn2:
            if st.session_state.result and not st.session_state.spinning:
                if st.button("🔄 Spin Again", use_container_width=True):
                    st.session_state.result = None
                    st.rerun()
    else:
        st.info("⚠️ No restaurants added yet! Admin needs to add some options.")

# Admin section
st.markdown("---")
st.markdown("### 🔧 Admin Panel")

if not st.session_state.authenticated:
    password = st.text_input("Enter admin password:", type="password", key="password_input")
    if st.button("Login"):
        if password == ADMIN_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password!")
else:
    st.success("✅ Authenticated as Admin")
    
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()
    
    # Add new restaurant
    st.markdown("#### ➕ Add Restaurant")
    col1, col2 = st.columns([3, 1])
    with col1:
        new_name = st.text_input("Restaurant name:", key="new_restaurant")
    with col2:
        new_prob = st.number_input("Probability:", min_value=1, max_value=100, value=10, key="new_prob")
    
    if st.button("Add Restaurant"):
        if new_name.strip():
            restaurants.append({
                "name": new_name.strip(),
                "probability": new_prob
            })
            save_restaurants(restaurants)
            st.success(f"Added {new_name}!")
            st.rerun()
        else:
            st.error("Please enter a restaurant name!")
    
    # Edit existing restaurants
    if restaurants:
        st.markdown("#### ✏️ Edit Restaurants")
        for idx, restaurant in enumerate(restaurants):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                new_name = st.text_input(
                    f"Name {idx + 1}:", 
                    value=restaurant['name'],
                    key=f"name_{idx}"
                )
            with col2:
                new_prob = st.number_input(
                    f"Prob {idx + 1}:",
                    min_value=1,
                    max_value=100,
                    value=restaurant['probability'],
                    key=f"prob_{idx}"
                )
            with col3:
                st.markdown("")
                st.markdown("")
                if st.button("🗑️", key=f"delete_{idx}"):
                    restaurants.pop(idx)
                    save_restaurants(restaurants)
                    st.rerun()
            
            # Update if changed
            if new_name != restaurant['name'] or new_prob != restaurant['probability']:
                restaurants[idx] = {
                    "name": new_name,
                    "probability": new_prob
                }
                save_restaurants(restaurants)

st.markdown("---")
st.caption("🎡 Fortune Wheel Restaurant Picker | Built with Streamlit")
