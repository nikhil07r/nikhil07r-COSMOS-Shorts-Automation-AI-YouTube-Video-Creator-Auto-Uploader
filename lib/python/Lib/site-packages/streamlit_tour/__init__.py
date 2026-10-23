from __future__ import annotations
from typing import Any
import streamlit.components.v2 as components
from importlib.metadata import version
from typing import Optional, Literal
import streamlit as st

__version__ = version("streamlit_tour")

# Register the component once at import time.
out = components.component(
    name="streamlit-tour.streamlit_tour",
    js="index-*.js",                # glob — matches the hashed vite output
)

def on_unused_state_change():
    pass

class Step:
    element: str
    popover: dict

    def __init__(self, element: str, popover: dict):
        self.element = element
        self.popover = popover
    
    def to_dict(self):
        if self.element:
            return {
                "element": self.element,
                "popover": self.popover
            }
        else:
            return {
                "popover": self.popover
            }

class TourStatus:
    """
    Object containing the status of a Driver.js tour.
    """
    currentStep: int
    dismissed: bool
    finished: bool
    skipped: bool

    def __init__(self, currentStep: int, dismissed: bool, finished: bool, skipped: bool):
        self.currentStep = currentStep
        self.dismissed = dismissed
        self.finished = finished
        self.skipped = skipped
    
    def to_dict(self):
        return {
            "currentStep": self.currentStep,
            "dismissed": self.dismissed,
            "finished": self.finished
        }
    

class Tour:
    STATE_PREFIX="stTour-"

    def __init__(
            self,
            steps: list,
            *,
            key: str = "tour",
            show_progress: bool = True,
            animate: bool = True,
            overlay_opacity: float = 0.75,
            one_time_tour: bool = False,
        ):
        """
        Initialize a Driver.js guided tour.

        Parameters
        ----------
        steps : list of Step, i.e. tour.bind(...)
        key : str, default="tour"
            Streamlit widget key.
        show_progress : bool
            Show "1/3" step counter in the popover.
        animate : bool
            Animate transitions between steps.
        overlay_opacity : float
            Background overlay opacity (0.0 - 1.0).
        one_time_tour : bool
            Whether to show the tour only once.
        """

        self.steps = steps
        self.key = key
        self.state_key = f"{self.STATE_PREFIX}-{self.key}-active"
        self.reset_key = f"{self.STATE_PREFIX}-{self.key}-reset"
        self.show_progress = show_progress
        self.animate = animate
        self.overlay_opacity = overlay_opacity
        self.one_time_tour = one_time_tour
        self.result = self._initialize_render()
    
    def _initialize_render(self) -> TourStatus | None:
        if self.state_key not in st.session_state:
            st.session_state[self.state_key] = False
        
        if self.reset_key not in st.session_state:
            st.session_state[self.reset_key] = False
        
        if st.session_state[self.reset_key]:
            out(
                data={
                    "steps": [],
                    "key": self.key,
                    "tourStorageKey": self.STATE_PREFIX + self.key,
                    "reset": True,
                },
                default={"currentStep": 0, "dismissed": False, "finished": False, "skipped": False},
                key=self.key,
                height=0,
                on_currentStep_change=on_unused_state_change,
                on_dismissed_change=on_unused_state_change,
                on_finished_change=on_unused_state_change,
                on_skipped_change=on_unused_state_change
            )
            st.session_state[self.reset_key] = False
            return None

        if not st.session_state[self.state_key]:
            return None
        
        component_value = out(
            data={
                "steps": [s.to_dict() for s in self.steps],
                "showProgress": self.show_progress,
                "animate": self.animate,
                "overlayOpacity": self.overlay_opacity,
                "oneTimeTour": self.one_time_tour,
                "key": self.key,
                "tourStorageKey": self.STATE_PREFIX + self.key,
                "reset": st.session_state[self.reset_key],
            },
            default={
                "currentStep": 0, 
                "dismissed": False,
                "finished": False,
                "skipped": False,
            },
            key=self.key,
            height=0,
            on_currentStep_change=on_unused_state_change,
            on_dismissed_change=on_unused_state_change,
            on_finished_change=on_unused_state_change,
            on_skipped_change=on_unused_state_change
        )

        result = TourStatus(**component_value)

        if result.finished or result.dismissed:
            st.session_state[self.state_key] = False
            st.rerun()
                    
        return result

    def __repr__(self):
        if self.result:
            return f"TourStatus(currentStep={self.result.currentStep}, dismissed={self.result.dismissed}, finished={self.result.finished}, skipped={self.result.skipped})"
        else:
            return "Tour not started yet"
        
    def start(self):
        st.session_state[self.state_key] = True
        st.rerun()

    def reset(self):
        """Clears the one-time-seen flag from localStorage so the tour shows again."""
        st.session_state[self.reset_key] = True
        st.rerun()

    @staticmethod
    def bind(
            key: str,
            title: str = "Title",
            desc: str = "Description",
            side: Optional[Literal["top", "bottom", "left", "right"]] = None,
            align: Optional[Literal["start", "center", "end"]] = None,
            ):
        """
        Binds a streamlit component to a step in the tour.
        """
        if side is None and align is None:
            return Step(".st-key-" + key, {"title": title, "description": desc})
        elif side is None and align is not None:
            return Step(".st-key-" + key, {"title": title, "description": desc, "align": align})
        elif side is not None and align is None:
            return Step(".st-key-" + key, {"title": title, "description": desc, "side": side})
        else:
            return Step(".st-key-" + key, {"title": title, "description": desc, "side": side, "align": align})
    
    @staticmethod
    def info(
            title: str = "Title",
            desc: str = "Description",
            ):
        return Step("", {"title": title, "description": desc})
    