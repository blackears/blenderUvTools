# This file is part of the Kitfox Normal Brush distribution (https://github.com/blackears/blenderUvTools).
# Copyright (c) 2021 Mark McKay
# 
# This program is free software: you can redistribute it and/or modify  
# it under the terms of the GNU General Public License as published by  
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU 
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License 
# along with this program. If not, see <http://www.gnu.org/licenses/>.


bl_info = {
    "name": "Uv Tools",
    "description": "Tools for editing UVs in the viewport.",
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
        
    if "triplanarUvUnwrap" in locals():
        importlib.reload(triplanarUvUnwrap)
    else:
        from .operators import triplanarUvUnwrap
        
    if "copySymmetricUvs" in locals():
        importlib.reload(copySymmetricUvs)
    else:
        from .operators import copySymmetricUvs
        
    if "uvToolsPanel" in locals():
        importlib.reload(uvToolsPanel)
    else:
        from .operators import uvToolsPanel
        
else:
    from .operators import uvBrushTool
    from .operators import triplanarUvUnwrap
    from .operators import copySymmetricUvs
    from .operators import uvLayoutPlane
    from .operators import uvToolsPanel

def register():
    uvBrushTool.register()
    triplanarUvUnwrap.register()
    copySymmetricUvs.register()
    uvLayoutPlane.register()
    uvToolsPanel.register()


def unregister():
    uvBrushTool.unregister()
    triplanarUvUnwrap.unregister()
    copySymmetricUvs.unregister()
    uvLayoutPlane.unregister()
    uvToolsPanel.unregister()

