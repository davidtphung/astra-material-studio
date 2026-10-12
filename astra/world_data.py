"""Deterministic fictional rooftop set. Metres, Y-up, shared by web and Blender."""
import math
import random


def build_world(seed=42):
    rng = random.Random(seed)
    palette = {
        'repair': {'color':'#828476','roughness':.97,'surface':'stone'},
        'stain': {'color':'#555d50','roughness':.94,'surface':'stone'},
        'concrete': {'color':'#6d7067','roughness':.9,'surface':'stone'},
        'tile': {'color':'#7b8174','roughness':.85,'surface':'stone'},
        'tile2': {'color':'#777b6d','roughness':.88,'surface':'stone'},
        'grout': {'color':'#333c36','roughness':1},
        'plaster': {'color':'#898a75','roughness':.95,'surface':'stone'},
        'plaster2': {'color':'#657574','roughness':.95,'surface':'stone'},
        'plaster3': {'color':'#a78c78','roughness':.93,'surface':'stone'},
        'trim': {'color':'#424f49','roughness':.68,'metalness':.45},
        'steel': {'color':'#727f7a','roughness':.38,'metalness':.9},
        'rust': {'color':'#805038','roughness':.85,'metalness':.25,'surface':'stone'},
        'wood': {'color':'#6d4b32','roughness':.8,'surface':'wood'},
        'wood2': {'color':'#8a6747','roughness':.75,'surface':'wood'},
        'rubber': {'color':'#202725','roughness':.95},
        'glass': {'color':'#213c3e','roughness':.2,'metalness':.4},
        'warm_window': {'color':'#b69058','roughness':.5,'emissive':'#ffc97b','emission':.6},
        'cool_window': {'color':'#7b9d96','roughness':.5,'emissive':'#b0e5de','emission':.25},
        'orange': {'color':'#b66533','roughness':.75},
        'white': {'color':'#c5c5ac','roughness':.65},
        'neon': {'color':'#cef49c','roughness':.4,'emissive':'#d6ffac','emission':2},
        'red_neon': {'color':'#ea866e','roughness':.4,'emissive':'#ff8765','emission':1.6},
        'leaf': {'color':'#425e32','roughness':.8},
        'terracotta': {'color':'#8e5c3e','roughness':.9},
        'cloth': {'color':'#9caa99','roughness':1},
        'blue_cloth': {'color':'#527778','roughness':1},
        'water': {'color':'#4f625e','roughness':.1,'metalness':.35},
        'paper': {'color':'#c7bea0','roughness':.95},
    }
    objects=[]
    def add(name,material,position,size,geometry='box',rotation=None):
        item={'name':name,'material':material,'position':position,'size':size,'geometry':geometry}
        if rotation:
            item['rotation']=rotation
        objects.append(item)
        return item
    def rod(name,material,start,end,radius=.025):
        item={'name':name,'material':material,'start':start,'end':end,'radius':radius,'geometry':'rod'}
        objects.append(item)
    # A 16 x 14 metre inhabited roof, with slab thickness and tiled drainage slopes implied.
    # The roof belongs to an actual supporting building, down to street level.
    add('Neighbourhood street surface','grout',[0,-8.45,0],[160,.2,160])
    add('Host building structure','plaster2',[0,-4.4,0],[16,7.8,14])
    add('Host building pavement','concrete',[0,-8.25,0],[17,.2,15])
    for y in [-6.6,-3.6]:
        for x in range(-7,8):
            add('Host front window frame','trim',[x,y,7.06],[.8,1.6,.12])
            add('Host front window','glass',[x,y,7.133],[.68,1.44,.025])
        for side in [-1,1]:
            for z in range(-6,7):
                add('Host side window frame','trim',[side*8.06,y,z],[.12,1.6,.8])
                add('Host side window','glass',[side*8.133,y,z],[.025,1.44,.68])
    add('Structural roof slab','concrete',[0,-.25,0],[16,.5,14])
    add('Roof tile grout','grout',[0,.006,0],[16,.02,14])
    for x in range(-8,8):
        for z in range(-7,7):
            add('Weathered roof tile','tile' if rng.random()>.3 else 'tile2',[x+.5,.024,z+.5],[.979,.035,.979])
    for x in [-7.9,7.9]:
        add('Side parapet','concrete',[x,.5,0],[.2,1,14])
        add('Parapet cap','plaster',[x,1.02,0],[.28,.1,14])
    add('Back parapet','concrete',[0,.5,-6.9],[16,1,.2])
    add('Back cap','plaster',[0,1.02,-6.9],[16,.1,.3])
    for x in range(-7,8,2):
        rod('Safety railing post','steel',[x,1,-6.9],[x,1.85,-6.9])
    for y in [1.4,1.85]:
        rod('Safety railing','steel',[-7.7,y,-6.9],[7.7,y,-6.9])
    # Small repaired patches and utility conduits break the pristine roof edges.
    for x in [-6.5,-2.3,1.7,5.6]:
        add('Parapet repair patch','repair',[x,.38,-6.785],[.5,.36,.012])
        add('Rain runoff stain','stain',[x+.13,.2,-6.776],[.045,.26,.008])
    for y in [.24,.33]:
        rod('Wall-mounted service conduit','rust',[-7.75,y,-6.75],[7.7,y,-6.75],.014)
    # Workbench: 0.90 m top, welded frame, boards and a lower shelf.
    for x in [-1.35,1.35]:
        for z in [-.55,.55]:
            add('Workbench steel leg','trim',[x,.44,z],[.08,.84,.08])
            add('Workbench foot','rubber',[x,.06,z],[.14,.06,.14])
    for z in [-.57,.57]:
        add('Workbench apron','trim',[0,.76,z],[2.85,.16,.065])
        add('Shelf rail','trim',[0,.23,z],[2.85,.07,.07])
    for i in range(7):
        add('Workbench top plank','wood2' if i%3 else 'wood',[0,.86,-.63+i*.21],[3.2,.08,.199])
        for x in [-1.39,1.39]:
            add('Recessed fastener','steel',[x,.904,-.63+i*.21],[.017,.005,.017],'cylinder')
    add('Lower shelf','wood', [0,.25,0],[2.7,.045,1.1])
    add('Sample support','concrete',[0,.945,0],[1.15,.09,.9])
    add('Small measurement rule','steel',[.18,.91,.53],[1.35,.007,.04])
    for i in range(31):
        add('Rule engraving','rubber',[-.43+i*.04,.915,.53],[.003,.003,.033 if i%5==0 else .017])
    add('Notebook','paper',[-1.05,.925,.13],[.34,.04,.25],rotation=[0,.2,0])
    add('Glove one','orange',[1.16,.925,.31],[.13,.035,.24],rotation=[0,.4,0])
    add('Glove two','orange',[1.32,.925,.25],[.13,.035,.24],rotation=[0,-.2,0])
    add('Paint tin','steel',[-1.16,1.04,-.39],[.2,.27,.2],'cylinder')
    add('Paint tin label','white',[-1.16,1.04,-.39],[.203,.12,.203],'cylinder')
    for x in [-.8,-.35,.1]:
        add('Underbench stock box','wood2',[x,.42,0],[.4,.29,.65])
    # Everyday props establish human scale.
    for x,z in [(2.3,.35),(-2.35,.8)]:
        add('Stool seat','wood2',[x,.55,z],[.48,.06,.48],'cylinder')
        for angle in [0,2.094,4.188]:
            rod('Stool leg','trim',[x+math.sin(angle)*.17,.52,z+math.cos(angle)*.17],[x+math.sin(angle)*.25,.055,z+math.cos(angle)*.25],.024)
    for cx,cz,levels in [(-4.8,-3.6,2),(4.7,-3.2,1)]:
        for level in range(levels):
            cy=.31+level*.58
            add('Shipping crate core','wood',[cx,cy,cz],[.9,.54,.7])
            for xx in [-.36,.36]:
                add('Crate vertical brace','wood2',[cx+xx,cy,cz+.36],[.1,.56,.04])
            for yy in [-.2,.2]:
                add('Crate horizontal brace','wood2',[cx,cy+yy,cz+.385],[.93,.09,.04])
    for x,z in [(-3,-1.5),(3.3,-2.2)]:
        add('Traffic cone base','rubber',[x,.06,z],[.36,.04,.36])
        add('Traffic cone','orange',[x,.29,z],[.23,.46,.23],'cone')
        add('Cone reflective band','white',[x,.34,z],[.112,.07,.112],'cylinder')
    for x,z in [(5.8,-5),(-6.3,-1)]:
        add('Plant pot','terracotta',[x,.27,z],[.6,.48,.6],'cylinder')
        add('Plant soil','rubber',[x,.515,z],[.52,.015,.52],'cylinder')
        for j in range(13):
            a=j*2.399
            h=rng.uniform(.45,.95)
            start=[x,.52,z]
            end=[x+math.cos(a)*.35,h+.52,z+math.sin(a)*.35]
            rod('Plant stem','leaf',start,end,.012)
            add('Plant leaf','leaf',end,[.19,.035,.46],'sphere',[.4,a,.3])
    # Mechanical service area at rear left.
    add('Rooftop service room','plaster2',[-5.2,1.75,-5.3],[3.4,3.5,2.5])
    add('Service room roof','concrete',[-5.2,3.55,-5.3],[3.6,.2,2.7])
    add('Steel access door','trim',[-5.7,1.1,-4.034],[.9,2.15,.06])
    add('Door vision panel','glass',[-5.7,1.55,-3.99],[.6,.5,.025])
    add('Door lever','steel',[-5.39,1.05,-3.97],[.13,.025,.06])
    for x in [-4.6,-3.65]:
        add('Outdoor AC cabinet','white',[x,.5,-3.7],[.8,.88,.5])
        add('AC fan recess','trim',[x,.53,-3.438],[.55,.55,.04],'cylinder',[math.pi/2,0,0])
        for j in range(9):
            add('AC protective grille','steel',[x-.28+j*.07,.53,-3.398],[.012,.65,.022])
        rod('AC refrigerant pipe','rust',[x-.3,.35,-3.8],[x-.3,.35,-6],.032)
    add('Water tank','steel',[-5.1,4.5,-5.4],[1.5,1.5,1.5],'cylinder')
    add('Tank lid','trim',[-5.1,5.27,-5.4],[1.55,.07,1.55],'cylinder')
    for y in [3.9,4.3,4.7,5.1]:
        add('Tank reinforcement hoop','trim',[-5.1,y,-5.4],[1.53,.035,1.53],'cylinder')
    rod('Tank feed pipe','rust',[-5.85,4.4,-5.4],[-5.85,.3,-5.4],.04)
    # Task lamp is visibly connected to its source of light.
    rod('Task lamp mast','steel',[-1.38,.91,-.49],[-1.38,2.22,-.49],.023)
    rod('Task lamp arm','steel',[-1.38,2.22,-.49],[-.53,2.22,-.49],.023)
    add('Task lamp housing','trim',[-.53,2.19,-.49],[.53,.13,.17])
    add('Task lamp diffuser','neon',[-.53,2.117,-.49],[.45,.02,.13])
    # Sagging cables cross the skyline; laundry is stationary unless animation is enabled.
    for z in [-3.5,-5.9]:
        for x in [-2.8,6.7]:
            rod('Laundry post','rust',[x,.05,z],[x,2.75,z],.026)
        for i in range(18):
            x1=-2.8+i*9.5/18
            x2=-2.8+(i+1)*9.5/18
            h=lambda x:2.75-.24*math.sin((x+2.8)/9.5*math.pi)
            rod('Sagging laundry line','rubber',[x1,h(x1),z],[x2,h(x2),z],.008)
    for j,x in enumerate([2.9,3.6,4.3,5.15,5.9]):
        add('Hanging cloth','cloth' if j%2 else 'blue_cloth',[x,2.13,-5.9],[.5,.85 if j%2 else 1.05,.018],rotation=[0,.08*j,0])
    # Drain and rainwater collect away from the workbench.
    for x,z in [(-6,3),(5,2.8)]:
        add('Drain frame','trim',[x,.058,z],[.8,.03,.4])
        for j in range(10):
            add('Drain slot','rubber',[x-.34+j*.075,.077,z],[.04,.008,.32])
    for x,z,sx,sz in [(-3.8,2.5,2.5,.7),(3.4,2.1,2.2,.95),(.5,-2.6,3.2,.65),(-6,-2,1.5,.9)]:
        add('Rainwater puddle','water',[x,.049,z],[sx,.008,sz],'sphere')
    # Dense fictional city massing: real dimensions, not a reconstruction of a real address.
    towers=[(-12,-11,7,21,6),(-4,-13,6,26,5),(3,-13,6,19,5),(10,-12,6,30,6),(15,-5,5,24,6),(-14,-3,5,17,6),(-20,-21,7,34,6),(-10,-25,7,37,7),(1,-24,8,39,6),(13,-25,7,43,7),(22,-18,6,32,6)]
    for index,(x,z,w,h,d) in enumerate(towers):
        bottom=-8
        add(f'Neighbourhood tower {index+1}', ['plaster','plaster2','plaster3'][index%3],[x,h/2+bottom,z],[w,h,d])
        for y in range(-5,int(h+bottom),3):
            add('Facade floor band','concrete',[x,y,z+d/2+.025],[w+.08,.12,.08])
            for dx in range(int(w)-1):
                wx=x-w/2+1+dx
                mat=rng.choices(['glass','warm_window','cool_window'],[.48,.39,.13])[0]
                add('Recessed apartment window frame','trim',[wx,y+1.1,z+d/2+.075],[.8,1.6,.12])
                add('Apartment window',''+mat,[wx,y+1.1,z+d/2+.146],[.68,1.44,.025])
                add('Window mullion','trim',[wx,y+1.1,z+d/2+.17],[.035,1.5,.035])
                if index<6 and rng.random()<.1:
                    add('Apartment balcony slab','concrete',[wx,y+.2,z+d/2+.6],[1.05,.13,1])
                    for bx in [-.47,.47]:
                        rod('Balcony upright','trim',[wx+bx,y+.25,z+d/2+1.05],[wx+bx,y+1.15,z+d/2+1.05],.018)
                    rod('Balcony handrail','trim',[wx-.5,y+1.15,z+d/2+1.05],[wx+.5,y+1.15,z+d/2+1.05],.02)
                    for bx in [-.25,0,.25]:
                        rod('Balcony infill','trim',[wx+bx,y+.25,z+d/2+1.05],[wx+bx,y+1.15,z+d/2+1.05],.01)
                if rng.random()<.22 and not (index==2 and y==4):
                    add('Facade AC box','white',[wx,y-.1,z+d/2+.35],[.65,.4,.55])
        # Side elevations remain detailed when orbiting the set.
        for side in [-1,1]:
            for y in range(-5,int(h+bottom),3):
                for dz in range(1,int(d)-1):
                    wz=z-d/2+dz+.35
                    wx=x+side*(w/2+.06)
                    add('Side window frame','trim',[wx,y+1.1,wz],[.12,1.6,.8])
                    add('Side apartment window',rng.choice(['glass','glass','warm_window']),[wx+side*.073,y+1.1,wz],[.025,1.44,.68])
        for dx in [-w/2+.17,w/2-.17]:
            rod('Building drain stack','rust',[x+dx,bottom,z+d/2+.25],[x+dx,h+bottom,z+d/2+.25],.045)
        add('Roof cornice','concrete',[x,h+bottom+.1,z],[w+.3,.2,d+.3])
        for dx in [-.7,.7]:
            rod('Rooftop antenna mast','steel',[x+dx,h+bottom,z],[x+dx,h+bottom+2,z],.018)
            for y in [.6,1.1,1.6]:
                rod('Antenna crossbar','steel',[x+dx-.5,h+bottom+y,z],[x+dx+.5,h+bottom+y,z],.012)
    # Green practical sign on a nearby facade.
    add('Workshop sign backboard','trim',[2.8,3.9,-10.37],[3.2,1.1,.15])
    for x in [1.26,4.34]:
        add('Sign lit edge','neon',[x,3.9,-10.27],[.035,1,.035])
    for y in [3.42,4.38]:
        add('Sign lit edge','neon',[2.8,y,-10.27],[3.1,.035,.035])
    labels=[
        {'text':'ASTRA','position':[2.8,4,-10.25],'width':2.6,'height':.65,'color':'#d6ffac','background':'#20382e'},
        {'text':'SURFACE WORKS / 07','position':[-5.3,2.65,-4.025],'width':2.6,'height':.4,'color':'#d4d3b7','background':'#263d39'},
        {'text':'ASTRA  /  FIELD SAMPLE','position':[0,.72,.618],'width':1.25,'height':.13,'color':'#e0d9bd','background':'#314338'},
    ]
    return {'version':1,'seed':seed,'units':'metres','up':'Y','title':'Kowloon Rooftop / Surface Works 07','fictional':True,'palette':palette,'objects':objects,'labels':labels,'hero':{'support':.99,'scale':.48},'cameras':{'detail':{'position':[2.45,2.15,3.15],'target':[0,1.5,0]},'bench':{'position':[4.7,3.15,6.1],'target':[0,1.4,-.5]},'wide':{'position':[10.3,6.8,12.8],'target':[-.3,3.5,-2.5]}}}
