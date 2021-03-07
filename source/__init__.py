# Copyright 2021 Mark McKay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


bl_info = {
    "name": "Uv Tools",
    "description": "Tools to help lay in blocks.",
    "author": "Mark McKay",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "location": "View3D",
#    "wiki_url": "https://github.com/blackears/uvTools",
#    "tracker_url": "https://github.com/blackears/uvTools",
    "category": "View 3D"
}

import bpy
import importlib


if "bpy" in locals():
    if "uvBrushTool" in locals():
        importlib.reload(uvBrushTool)
    else:
        from .operators import uvBrushTool

    if "uvLayoutPlane" in locals():
        importlib.reload(uvLayoutPlane)
    else:
        from .operators import uvLayoutPlane
        
    if "uvToolsPanel" in locals():
        importlib.reload(uvToolsPanel)
    else:
        from .operators import uvToolsPanel
        
else:
    from .operators import uvBrushTool
    from .operators import uvLayoutPlane
    from .operators import uvToolsPanel

def register():
    uvBrushTool.register()
    uvLayoutPlane.register()
    uvToolsPanel.register()


def unregister():
    uvBrushTool.unregister()
    uvLayoutPlane.unregister()
    uvToolsPanel.unregister()

