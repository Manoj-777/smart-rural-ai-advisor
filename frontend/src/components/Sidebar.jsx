// src/components/Sidebar.jsx

import { NavLink } from 'react-router-dom';

function Sidebar() {
    return (
        <nav className="sidebar">
            <h1>🌾 Smart Rural AI</h1>
            <NavLink to="/" className={({isActive}) => isActive ? 'active' : ''}>
                💬 Chat Advisor
            </NavLink>
            <NavLink to="/weather" className={({isActive}) => isActive ? 'active' : ''}>
                🌤️ Weather
            </NavLink>
            <NavLink to="/schemes" className={({isActive}) => isActive ? 'active' : ''}>
                📋 Govt Schemes
            </NavLink>
            <NavLink to="/crop-doctor" className={({isActive}) => isActive ? 'active' : ''}>
                📸 Crop Doctor
            </NavLink>
            <NavLink to="/profile" className={({isActive}) => isActive ? 'active' : ''}>
                👤 My Farm
            </NavLink>
            <div style={{marginTop: 'auto', fontSize: '12px', opacity: 0.6}}>
                📞 Kisan Helpline: 1800-180-1551
            </div>
        </nav>
    );
}

export default Sidebar;
