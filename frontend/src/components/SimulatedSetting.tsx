import React, { useState } from 'react';
import { X, ArrowLeft, Check, Battery, Sun, HardDrive, Cpu } from 'lucide-react';
import type { Action } from '../types/api';

interface SimulatedSettingProps {
  action: Action;
  onClose: () => void;
  onMarkChecked: () => void;
}

export const SimulatedSetting: React.FC<SimulatedSettingProps> = ({
  action,
  onClose,
  onMarkChecked,
}) => {
  const [toggleState1, setToggleState1] = useState(true);
  const [toggleState2, setToggleState2] = useState(false);
  const [sliderVal, setSliderVal] = useState(70);
  const [selectedRadio, setSelectedRadio] = useState('option1');

  const targetScreen = action.target_screen;

  // Render specific simulated settings screen content
  const renderSettingBody = () => {
    switch (targetScreen) {
      case 'Battery > Battery usage':
        return (
          <div>
            <div className="setting-card" style={{ textAlign: 'center', padding: '1.5rem 1rem' }}>
              <Battery size={36} color="#0381fe" style={{ margin: '0 auto 0.5rem' }} />
              <div style={{ fontSize: '1.75rem', fontWeight: 800 }}>72%</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                Estimated 14 hrs 20 mins remaining
              </div>
              <div className="progress-bar-bg" style={{ marginTop: '0.75rem' }}>
                <div className="progress-bar-fill" style={{ width: '72%' }} />
              </div>
            </div>

            <div className="setting-section-title">Battery usage since last full charge</div>
            <div className="setting-card">
              <div className="setting-row">
                <span>Social Feed App</span>
                <span style={{ fontWeight: 700, color: 'var(--primary)' }}>28%</span>
              </div>
              <div className="progress-bar-bg"><div className="progress-bar-fill" style={{ width: '28%' }} /></div>

              <div className="setting-row" style={{ marginTop: '0.75rem' }}>
                <span>Video Streaming</span>
                <span style={{ fontWeight: 700 }}>17%</span>
              </div>
              <div className="progress-bar-bg"><div className="progress-bar-fill" style={{ width: '17%' }} /></div>

              <div className="setting-row" style={{ marginTop: '0.75rem' }}>
                <span>Web Browser</span>
                <span style={{ fontWeight: 700 }}>11%</span>
              </div>
              <div className="progress-bar-bg"><div className="progress-bar-fill" style={{ width: '11%' }} /></div>

              <div className="setting-row" style={{ marginTop: '0.75rem' }}>
                <span>One UI System & Display</span>
                <span style={{ fontWeight: 700 }}>8%</span>
              </div>
              <div className="progress-bar-bg"><div className="progress-bar-fill" style={{ width: '8%' }} /></div>
            </div>
          </div>
        );

      case 'Battery > Charging':
        return (
          <div>
            <div className="setting-card">
              <div className="setting-row">
                <div>
                  <div style={{ fontWeight: 700 }}>Fast charging</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Allow quick charging with supported adapters
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={toggleState1}
                  onChange={(e) => setToggleState1(e.target.checked)}
                  style={{ width: '20px', height: '20px', cursor: 'pointer' }}
                />
              </div>

              <div className="setting-row" style={{ marginTop: '1rem' }}>
                <div>
                  <div style={{ fontWeight: 700 }}>Fast wireless charging</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Accelerate wireless pad power delivery
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={toggleState2}
                  onChange={(e) => setToggleState2(e.target.checked)}
                  style={{ width: '20px', height: '20px', cursor: 'pointer' }}
                />
              </div>
            </div>
            <div className="setting-card">
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                ⚡ Connected Charger: Fast Charger (25W Adaptive)
              </div>
            </div>
          </div>
        );

      case 'Battery > Power saving':
        return (
          <div>
            <div className="setting-card">
              <div className="setting-row">
                <div>
                  <div style={{ fontWeight: 700 }}>Power saving mode</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Extend battery by limiting network and CPU
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={toggleState1}
                  onChange={(e) => setToggleState1(e.target.checked)}
                  style={{ width: '20px', height: '20px', cursor: 'pointer' }}
                />
              </div>
            </div>

            <div className="setting-section-title">Power saving options</div>
            <div className="setting-card">
              <div className="setting-row">
                <span>Limit CPU speed to 70%</span>
                <input type="checkbox" defaultChecked />
              </div>
              <div className="setting-row">
                <span>Decrease brightness by 10%</span>
                <input type="checkbox" defaultChecked />
              </div>
              <div className="setting-row">
                <span>Limit apps and Home screen</span>
                <input type="checkbox" />
              </div>
            </div>
          </div>
        );

      case 'Display > Brightness':
        return (
          <div>
            <div className="setting-card">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                <Sun size={20} color="#f59e0b" />
                <span style={{ fontWeight: 700 }}>Brightness Level ({sliderVal}%)</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={sliderVal}
                onChange={(e) => setSliderVal(Number(e.target.value))}
                style={{ width: '100%', cursor: 'pointer' }}
              />
            </div>

            <div className="setting-card">
              <div className="setting-row">
                <div>
                  <div style={{ fontWeight: 700 }}>Adaptive brightness</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Automatically adjust to ambient lighting
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={toggleState1}
                  onChange={(e) => setToggleState1(e.target.checked)}
                  style={{ width: '20px', height: '20px', cursor: 'pointer' }}
                />
              </div>
            </div>
          </div>
        );

      case 'Display > Screen timeout':
        return (
          <div>
            <div className="setting-section-title">Screen timeout duration</div>
            <div className="setting-card">
              {['15 seconds', '30 seconds', '1 minute', '2 minutes', '5 minutes', '10 minutes'].map((duration, i) => (
                <label
                  key={i}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.6rem 0',
                    borderBottom: i < 5 ? '1px solid var(--border-light)' : 'none',
                    cursor: 'pointer',
                  }}
                >
                  <span>{duration}</span>
                  <input
                    type="radio"
                    name="timeout"
                    checked={selectedRadio === duration || (selectedRadio === 'option1' && i === 2)}
                    onChange={() => setSelectedRadio(duration)}
                  />
                </label>
              ))}
            </div>
          </div>
        );

      case 'Display > Navigation':
        return (
          <div>
            <div className="setting-section-title">Navigation type</div>
            <div className="setting-card">
              <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.75rem 0', borderBottom: '1px solid var(--border-light)', cursor: 'pointer' }}>
                <div>
                  <div style={{ fontWeight: 700 }}>Swipe gestures</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Swipe from bottom and sides</div>
                </div>
                <input
                  type="radio"
                  name="nav"
                  checked={selectedRadio === 'gestures' || selectedRadio === 'option1'}
                  onChange={() => setSelectedRadio('gestures')}
                />
              </label>

              <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.75rem 0', cursor: 'pointer' }}>
                <div>
                  <div style={{ fontWeight: 700 }}>Buttons</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Classic 3-button navigation bar</div>
                </div>
                <input
                  type="radio"
                  name="nav"
                  checked={selectedRadio === 'buttons'}
                  onChange={() => setSelectedRadio('buttons')}
                />
              </label>
            </div>
          </div>
        );

      case 'Display > Touch settings':
        return (
          <div>
            <div className="setting-card">
              <div className="setting-row">
                <div>
                  <div style={{ fontWeight: 700 }}>Touch sensitivity</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Increase sensitivity for use with screen protectors
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={toggleState1}
                  onChange={(e) => setToggleState1(e.target.checked)}
                  style={{ width: '20px', height: '20px', cursor: 'pointer' }}
                />
              </div>
            </div>
          </div>
        );

      case 'Display > Screen mode':
        return (
          <div>
            <div className="setting-section-title">Screen color mode</div>
            <div className="setting-card">
              <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.6rem 0', borderBottom: '1px solid var(--border-light)', cursor: 'pointer' }}>
                <span>Vivid (saturated colors)</span>
                <input
                  type="radio"
                  name="screen_mode"
                  checked={selectedRadio === 'vivid' || selectedRadio === 'option1'}
                  onChange={() => setSelectedRadio('vivid')}
                />
              </label>
              <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.6rem 0', cursor: 'pointer' }}>
                <span>Natural (standard color space)</span>
                <input
                  type="radio"
                  name="screen_mode"
                  checked={selectedRadio === 'natural'}
                  onChange={() => setSelectedRadio('natural')}
                />
              </label>
            </div>

            <div className="setting-card">
              <div style={{ fontWeight: 700, marginBottom: '0.5rem' }}>White Balance</div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                <span>Cool (Blue)</span>
                <span>Warm (Amber)</span>
              </div>
              <input type="range" min="0" max="100" defaultValue="50" style={{ width: '100%', marginTop: '0.25rem' }} />
            </div>
          </div>
        );

      case 'Display > Accidental touch protection':
        return (
          <div>
            <div className="setting-card">
              <div className="setting-row">
                <div>
                  <div style={{ fontWeight: 700 }}>Accidental touch protection</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Protect screen from touches when phone is in pocket or bag
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={toggleState1}
                  onChange={(e) => setToggleState1(e.target.checked)}
                  style={{ width: '20px', height: '20px', cursor: 'pointer' }}
                />
              </div>
            </div>
            <div className="setting-card" style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              🛡️ Proximity sensor: Active and monitoring dark enclosures.
            </div>
          </div>
        );

      case 'Camera > Camera settings':
        return (
          <div>
            <div className="setting-card">
              <div className="setting-row">
                <span>Scene optimizer</span>
                <input type="checkbox" defaultChecked />
              </div>
              <div className="setting-row">
                <span>Auto HDR</span>
                <input type="checkbox" defaultChecked />
              </div>
              <div className="setting-row">
                <span>Grid lines</span>
                <input type="checkbox" />
              </div>
            </div>

            <div className="setting-card">
              <button
                className="btn-secondary"
                style={{ width: '100%', justifyContent: 'center', color: 'var(--danger)', borderColor: '#fca5a5' }}
                onClick={() => alert('Prototype: Camera settings reset to factory defaults.')}
              >
                Reset camera settings
              </button>
            </div>
          </div>
        );

      case 'Camera > Storage':
        return (
          <div>
            <div className="setting-section-title">Save location</div>
            <div className="setting-card">
              <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.6rem 0', borderBottom: '1px solid var(--border-light)' }}>
                <span>Internal storage</span>
                <input type="radio" name="cam_storage" defaultChecked />
              </label>
              <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.6rem 0' }}>
                <span>SD Card</span>
                <input type="radio" name="cam_storage" />
              </label>
            </div>
          </div>
        );

      case 'Settings > App permissions > Camera':
        return (
          <div>
            <div className="setting-section-title">Camera Permission Access</div>
            <div className="setting-card">
              <div className="setting-row">
                <span>Camera App</span>
                <span style={{ color: 'var(--success)', fontWeight: 700, fontSize: '0.85rem' }}>Allowed</span>
              </div>
              <div className="setting-row">
                <span>Social App</span>
                <span style={{ color: 'var(--success)', fontWeight: 700, fontSize: '0.85rem' }}>Only while in use</span>
              </div>
              <div className="setting-row">
                <span>Messaging App</span>
                <span style={{ color: 'var(--danger)', fontWeight: 700, fontSize: '0.85rem' }}>Denied</span>
              </div>
            </div>
          </div>
        );

      case 'Device care > Performance':
        return (
          <div>
            <div className="setting-card" style={{ textAlign: 'center', padding: '1.25rem' }}>
              <Cpu size={32} color="#0381fe" style={{ margin: '0 auto 0.5rem' }} />
              <div style={{ fontSize: '1.25rem', fontWeight: 800 }}>All systems normal</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Auto optimization enabled</div>
            </div>
            <div className="setting-card">
              <div className="setting-row">
                <span>Auto restart when needed</span>
                <input type="checkbox" defaultChecked />
              </div>
            </div>
          </div>
        );

      case 'Device care > Memory':
        return (
          <div>
            <div className="setting-card" style={{ textAlign: 'center', padding: '1.25rem' }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 800 }}>5.2 GB / 8 GB</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Available RAM: 2.8 GB</div>
              <button
                className="btn-primary"
                style={{ margin: '1rem auto 0', padding: '0.5rem 1.25rem' }}
                onClick={() => alert('Prototype: Cleaned 850 MB background memory.')}
              >
                Clean now (+850 MB)
              </button>
            </div>
          </div>
        );

      case 'Device care > Storage':
        return (
          <div>
            <div className="setting-card" style={{ textAlign: 'center', padding: '1.25rem' }}>
              <HardDrive size={32} color="#0381fe" style={{ margin: '0 auto 0.5rem' }} />
              <div style={{ fontSize: '1.5rem', fontWeight: 800 }}>114.2 GB / 128 GB</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--danger)', fontWeight: 600 }}>Storage 89% full</div>
              <div className="progress-bar-bg" style={{ marginTop: '0.75rem' }}>
                <div className="progress-bar-fill" style={{ width: '89%', background: 'var(--danger)' }} />
              </div>
            </div>
          </div>
        );

      case 'Settings > Apps':
      default:
        return (
          <div>
            <div className="setting-section-title">Installed Applications</div>
            <div className="setting-card">
              <div className="setting-row">
                <span>Social App</span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>2.4 GB • High battery</span>
              </div>
              <div className="setting-row">
                <span>Game Utility</span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>4.1 GB • Heavy background</span>
              </div>
              <div className="setting-row">
                <span>Cloud Storage Sync</span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>1.2 GB • Auto syncing</span>
              </div>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="phone-mockup" onClick={(e) => e.stopPropagation()}>
        <div className="phone-notch">
          <div className="notch-pill" />
        </div>

        <div className="phone-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <button
              onClick={onClose}
              style={{ background: 'transparent', border: 'none', cursor: 'pointer', display: 'flex' }}
            >
              <ArrowLeft size={20} />
            </button>
            <span className="phone-title">{targetScreen.split('>').pop()?.trim() || 'Settings'}</span>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', cursor: 'pointer', display: 'flex' }}
          >
            <X size={20} />
          </button>
        </div>

        <div className="phone-body">
          <span className="simulated-badge">Prototype Simulated Screen</span>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.75rem', fontFamily: 'monospace' }}>
            {action.deeplink || `prototype://${targetScreen.toLowerCase().replace(/ > /g, '/')}`}
          </div>
          {renderSettingBody()}
        </div>

        <div className="phone-footer">
          <button
            className="btn-secondary"
            onClick={onClose}
            style={{ flex: 1, justifyContent: 'center' }}
          >
            Back to SmartGuide
          </button>
          <button
            className="btn-primary"
            onClick={() => {
              onMarkChecked();
              onClose();
            }}
            style={{ flex: 1, justifyContent: 'center' }}
          >
            <Check size={16} />
            <span>I Checked This</span>
          </button>
        </div>
      </div>
    </div>
  );
};
