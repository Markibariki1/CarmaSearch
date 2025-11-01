import pandas as pd
import numpy as np
import re
from typing import Dict, List, Tuple, Optional

class DescriptionDetector:
    """
    Simplified description detector that identifies key factors affecting vehicle pricing.
    
    Detects:
    - Repaint history (lackiert, neu lackiert, etc.)
    - Accident history (unfall, vorschaden, etc.)
    - Condition indicators (gepflegt, mängel, etc.)
    - Maintenance status (scheckheftgepflegt, wartung, etc.)
    """
    
    def __init__(self):
        # Repaint patterns with impact levels
        self.repaint_patterns = {
            'high_quality': [
                r'neu\s+lackiert', r'professionell\s+lackiert', r'original\s+lackiert',
                r'werkstatt\s+lackiert', r'fachgerecht\s+lackiert'
            ],
            'visible_repaint': [
                r'teilweise\s+lackiert', r'bereiche\s+lackiert', r'seitenteile\s+lackiert',
                r'stoßstange\s+lackiert', r'kotflügel\s+lackiert', r'haube\s+lackiert', r'heck\s+lackiert'
            ],
            'color_change': [
                r'komplett\s+lackiert', r'vollständig\s+lackiert', r'farbe\s+geändert',
                r'umbelackiert', r'neue\s+farbe', r'andere\s+farbe'
            ],
            'general_repaint': [
                r'lackiert', r'nachlackiert', r'überlackiert', r'ausgebessert\s+und\s+lackiert'
            ]
        }
        
        # Accident history patterns
        self.accident_patterns = {
            'no_accident': [
                r'unfallfrei', r'keine\s+unfälle', r'unfallfrei\s+gefahren'
            ],
            'minor_damage': [
                r'parkrempler', r'leichte\s+parkrempler', r'kleine\s+dellen',
                r'kratzer', r'oberflächliche\s+schäden'
            ],
            'moderate_damage': [
                r'vorschaden', r'leichte\s+schäden', r'ausgebessert',
                r'repariert', r'fachgerecht\s+repariert'
            ],
            'major_damage': [
                r'unfallschaden', r'schwerer\s+unfall', r'große\s+schäden',
                r'aufprall', r'kollision'
            ],
            'total_loss': [
                r'totalschaden', r'wiederaufgebaut', r'komplett\s+repariert',
                r'neuwertiger\s+zustand\s+nach\s+unfall'
            ]
        }
        
        # Condition patterns
        self.condition_patterns = {
            'excellent': [
                r'wie\s+neu', r'neuwertig', r'sehr\s+gepflegt',
                r'keine\s+mängel', r'einwandfreier\s+zustand'
            ],
            'good': [
                r'gepflegt', r'gut\s+gepflegt', r'sehr\s+gut',
                r'wenige\s+gebrauchsspuren', r'guter\s+zustand'
            ],
            'average': [
                r'gebrauchsspuren', r'altersbedingte\s+gebrauchsspuren',
                r'normale\s+gebrauchsspuren', r'durchschnittlicher\s+zustand'
            ],
            'poor': [
                r'starke\s+gebrauchsspuren', r'viele\s+kratzer', r'dellen',
                r'schlechter\s+zustand', r'stark\s+beansprucht'
            ]
        }
        
        # Maintenance patterns
        self.maintenance_patterns = {
            'excellent': [
                r'scheckheftgepflegt', r'vollständig\s+scheckheftgepflegt',
                r'alle\s+wartungen\s+gemacht', r'immer\s+beim\s+händler'
            ],
            'good': [
                r'regelmäßig\s+gewartet', r'wartung\s+immer\s+gemacht',
                r'tüv\s+neu', r'hu\s+neu'
            ],
            'poor': [
                r'wartungsstau', r'inspektionsstau', r'wartung\s+überfällig',
                r'ölwechsel\s+überfällig', r'lange\s+keine\s+wartung'
            ]
        }
    
    def detect_description_impact(self, description: str) -> Dict[str, any]:
        """
        Detect description-based factors affecting vehicle pricing.
        
        Args:
            description: Vehicle description text in German
            
        Returns:
            Dictionary with detection results and total impact
        """
        if not isinstance(description, str) or not description.strip():
            return {
                'repaint_detected': False,
                'accident_detected': False,
                'condition_detected': False,
                'maintenance_detected': False,
                'total_impact': 0.0,
                'confidence': 0.0
            }
        
        description_lower = description.lower()
        
        # Detect repaint
        repaint_info = self._detect_repaint(description_lower)
        
        # Detect accident history
        accident_info = self._detect_accident(description_lower)
        
        # Detect condition
        condition_info = self._detect_condition(description_lower)
        
        # Detect maintenance
        maintenance_info = self._detect_maintenance(description_lower)
        
        # Calculate total impact
        total_impact = (
            repaint_info['impact'] +
            accident_info['impact'] +
            condition_info['impact'] +
            maintenance_info['impact']
        )
        
        # Calculate confidence (weighted by impact magnitude)
        impacts = [repaint_info['impact'], accident_info['impact'], 
                  condition_info['impact'], maintenance_info['impact']]
        confidences = [repaint_info['confidence'], accident_info['confidence'],
                      condition_info['confidence'], maintenance_info['confidence']]
        
        total_weight = sum(abs(imp) for imp in impacts)
        if total_weight > 0:
            confidence = sum(abs(imp) * conf for imp, conf in zip(impacts, confidences)) / total_weight
        else:
            confidence = 0.0
        
        return {
            'repaint_detected': repaint_info['detected'],
            'repaint_type': repaint_info['type'],
            'repaint_impact': repaint_info['impact'],
            'accident_detected': accident_info['detected'],
            'accident_type': accident_info['type'],
            'accident_impact': accident_info['impact'],
            'condition_detected': condition_info['detected'],
            'condition_type': condition_info['type'],
            'condition_impact': condition_info['impact'],
            'maintenance_detected': maintenance_info['detected'],
            'maintenance_type': maintenance_info['type'],
            'maintenance_impact': maintenance_info['impact'],
            'total_impact': total_impact,
            'confidence': confidence
        }
    
    def _detect_repaint(self, description_lower: str) -> Dict[str, any]:
        """Detect repaint information."""
        for category, patterns in self.repaint_patterns.items():
            for pattern in patterns:
                if re.search(pattern, description_lower):
                    impact_map = {
                        'high_quality': 0.035,    # 3.5% - professional repaint
                        'visible_repaint': 0.075, # 7.5% - visible repaint
                        'color_change': 0.10,     # 10% - color change
                        'general_repaint': 0.075  # 7.5% - general repaint
                    }
                    return {
                        'detected': True,
                        'type': category,
                        'impact': impact_map[category],
                        'confidence': 0.8
                    }
        return {'detected': False, 'type': None, 'impact': 0.0, 'confidence': 0.0}
    
    def _detect_accident(self, description_lower: str) -> Dict[str, any]:
        """Detect accident history."""
        for category, patterns in self.accident_patterns.items():
            for pattern in patterns:
                if re.search(pattern, description_lower):
                    impact_map = {
                        'no_accident': 0.0,        # No impact - positive signal
                        'minor_damage': -0.05,     # -5% - minor damage
                        'moderate_damage': -0.10,  # -10% - moderate damage
                        'major_damage': -0.15,     # -15% - major damage
                        'total_loss': -0.20        # -20% - total loss
                    }
                    return {
                        'detected': True,
                        'type': category,
                        'impact': impact_map[category],
                        'confidence': 0.9
                    }
        return {'detected': False, 'type': None, 'impact': 0.0, 'confidence': 0.0}
    
    def _detect_condition(self, description_lower: str) -> Dict[str, any]:
        """Detect vehicle condition."""
        for category, patterns in self.condition_patterns.items():
            for pattern in patterns:
                if re.search(pattern, description_lower):
                    impact_map = {
                        'excellent': 0.08,   # +8% - excellent condition
                        'good': 0.03,        # +3% - good condition
                        'average': 0.0,      # 0% - average condition
                        'poor': -0.10        # -10% - poor condition
                    }
                    return {
                        'detected': True,
                        'type': category,
                        'impact': impact_map[category],
                        'confidence': 0.7
                    }
        return {'detected': False, 'type': None, 'impact': 0.0, 'confidence': 0.0}
    
    def _detect_maintenance(self, description_lower: str) -> Dict[str, any]:
        """Detect maintenance status."""
        for category, patterns in self.maintenance_patterns.items():
            for pattern in patterns:
                if re.search(pattern, description_lower):
                    impact_map = {
                        'excellent': 0.05,   # +5% - excellent maintenance
                        'good': 0.02,        # +2% - good maintenance
                        'poor': -0.08        # -8% - poor maintenance
                    }
                    return {
                        'detected': True,
                        'type': category,
                        'impact': impact_map[category],
                        'confidence': 0.8
                    }
        return {'detected': False, 'type': None, 'impact': 0.0, 'confidence': 0.0}
    
    def apply_description_adjustment(self, base_price: float, description_impact: float) -> float:
        """
        Apply description-based adjustment to base price.
        
        Args:
            base_price: Original price estimate
            description_impact: Total impact from description analysis
            
        Returns:
            Adjusted price after description impact
        """
        if description_impact == 0.0:
            return base_price
        
        # Apply impact as price adjustment
        adjustment_factor = 1.0 + description_impact
        adjusted_price = base_price * adjustment_factor
        
        return adjusted_price
    
    def process_dataframe(self, df: pd.DataFrame, description_col: str = 'description') -> pd.DataFrame:
        """
        Process entire dataframe to add description detection columns.
        
        Args:
            df: Input dataframe with vehicle data
            description_col: Name of description column
            
        Returns:
            Dataframe with added description detection columns
        """
        if description_col not in df.columns:
            print(f"Warning: Description column '{description_col}' not found in dataframe")
            return df
        
        # Apply description detection to all rows
        detection_results = df[description_col].apply(self.detect_description_impact)
        
        # Extract results into separate columns
        df_result = df.copy()
        
        # Add detection columns
        df_result['repaint_detected'] = [r['repaint_detected'] for r in detection_results]
        df_result['repaint_type'] = [r['repaint_type'] for r in detection_results]
        df_result['repaint_impact'] = [r['repaint_impact'] for r in detection_results]
        
        df_result['accident_detected'] = [r['accident_detected'] for r in detection_results]
        df_result['accident_type'] = [r['accident_type'] for r in detection_results]
        df_result['accident_impact'] = [r['accident_impact'] for r in detection_results]
        
        df_result['condition_detected'] = [r['condition_detected'] for r in detection_results]
        df_result['condition_type'] = [r['condition_type'] for r in detection_results]
        df_result['condition_impact'] = [r['condition_impact'] for r in detection_results]
        
        df_result['maintenance_detected'] = [r['maintenance_detected'] for r in detection_results]
        df_result['maintenance_type'] = [r['maintenance_type'] for r in detection_results]
        df_result['maintenance_impact'] = [r['maintenance_impact'] for r in detection_results]
        
        df_result['description_total_impact'] = [r['total_impact'] for r in detection_results]
        df_result['description_confidence'] = [r['confidence'] for r in detection_results]
        
        return df_result

def test_description_detector():
    """Test the description detector with sample German descriptions."""
    detector = DescriptionDetector()
    
    test_cases = [
        "BMW 320i, unfallfrei, checkheftgepflegt, wie neu, sehr gepflegt",
        "Audi A4, vorschaden, wartungsstau, gebrauchsspuren, schlechter zustand",
        "Mercedes C-Klasse, neu lackiert, technisch einwandfrei, gepflegt",
        "VW Golf, totalschaden wiederaufgebaut, motor läuft unrund, muss weg",
        "Opel Astra, teilweise lackiert, parkrempler, normale gebrauchsspuren"
    ]
    
    print("Description Detection Test Results:")
    print("=" * 60)
    
    for i, description in enumerate(test_cases, 1):
        result = detector.detect_description_impact(description)
        print(f"\nTest {i}: {description}")
        print(f"Total Impact: {result['total_impact']:+.1%}")
        print(f"Confidence: {result['confidence']:.1%}")
        
        if result['repaint_detected']:
            print(f"  Repaint: {result['repaint_type']} ({result['repaint_impact']:+.1%})")
        if result['accident_detected']:
            print(f"  Accident: {result['accident_type']} ({result['accident_impact']:+.1%})")
        if result['condition_detected']:
            print(f"  Condition: {result['condition_type']} ({result['condition_impact']:+.1%})")
        if result['maintenance_detected']:
            print(f"  Maintenance: {result['maintenance_type']} ({result['maintenance_impact']:+.1%})")

if __name__ == "__main__":
    test_description_detector()
