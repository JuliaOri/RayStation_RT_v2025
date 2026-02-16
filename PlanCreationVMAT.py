from raystation import *
import numpy as np
from raystation.v2025.typing.generated import DoseBasedRoiFunction
import tkinter as tk
from tkinter import messagebox, ttk

case = get_current('Case')
examAll=case.Examinations #objeto examination
examCurrent=get_current('Examination')
examCurrentName=examCurrent.Name #nombre de examination
# Selecciona automáticamente el que esté abierto, pero en la segunda ventana de selección te permite cambiarlo con la variable CT
examinationAll=[exam.Name for exam in examAll]

pm = case.PatientModel
rois = pm.RegionsOfInterest
external=[roi for roi in rois if roi.Type=='External'][0].Name #indice  esolo puede haber un external
RoisAll=[roi.Name for roi in rois] 

# arrays para las ventanas de selección del plan
Couches = ['None', 'Thin', 'Med', 'Thick']
Energias = ['6', '6 FFF']
Funciones_inicio = [ 'Min/Max DVH','Min/Max dose']
Acceleradores = ['TrueBeam1', 'TrueBeam3', 'TrueBeam4']
Arcos=[179,181] #como depende del plan, he decidido poner dos arcos completos con el colimador a 20 (aproximado a una próstata típica)
#a corregir por el físico
Colimador=20



def center_window(win):
    win.update_idletasks()
    w = win.winfo_width()
    h = win.winfo_height()
    ws = win.winfo_screenwidth()
    hs = win.winfo_screenheight()
    x = (ws // 2) - (w // 2)
    y = (hs // 2) - (h // 2)
    win.geometry(f'{w}x{h}+{x}+{y}')


def create_modal_window(title):
    win = tk.Tk()
    win.title(title)
    win.resizable(False, False)
    return win



def ventana_principal():
    win = create_modal_window("Datos del Plan")
    variables = {}

    # --- Variables Tkinter ---
    nombre_var = tk.StringVar(value="Plan")
    dosim_var = tk.StringVar(value="Dosimetrista")
    acc_var = tk.StringVar(value=Acceleradores[0])
    ener_var = tk.StringVar(value=Energias[0])
    couch_var = tk.StringVar(value=Couches[0])

    # --- CT actual como valor por defecto ---
    default_ct = examCurrentName if examCurrentName in examinationAll else (examinationAll[0] if examinationAll else "N/A")
    ct_var = tk.StringVar(value=default_ct)

    # --- Campos y etiquetas ---
    ttk.Label(win, text="Nombre del plan:").grid(row=0, column=0, sticky='w', padx=10, pady=5)
    e_nombre = ttk.Entry(win, textvariable=nombre_var)
    e_nombre.grid(row=0, column=1, padx=10, pady=5)
    e_nombre.focus()
    e_nombre.select_range(0, 'end')

    ttk.Label(win, text="Dosimetrista:").grid(row=1, column=0, sticky='w', padx=10, pady=5)
    e_dosim = ttk.Entry(win, textvariable=dosim_var)
    e_dosim.grid(row=1, column=1, padx=10, pady=5)

    ttk.Label(win, text="Acelerador:").grid(row=2, column=0, sticky='w', padx=10, pady=5)
    acc_cb = ttk.Combobox(win, values=Acceleradores, textvariable=acc_var, state='readonly')
    acc_cb.grid(row=2, column=1, padx=10, pady=5)
    acc_cb.current(0)

    ttk.Label(win, text="Energía:").grid(row=3, column=0, sticky='w', padx=10, pady=5)
    ener_cb = ttk.Combobox(win, values=Energias, textvariable=ener_var, state='readonly')
    ener_cb.grid(row=3, column=1, padx=10, pady=5)
    ener_cb.current(0)

    ttk.Label(win, text="Couch:").grid(row=4, column=0, sticky='w', padx=10, pady=5)
    couch_cb = ttk.Combobox(win, values=Couches, textvariable=couch_var, state='readonly')
    couch_cb.grid(row=4, column=1, padx=10, pady=5)
    couch_cb.current(0)

    ttk.Label(win, text="CT:").grid(row=5, column=0, sticky='w', padx=10, pady=5)
    ct_cb = ttk.Combobox(win, values=examinationAll, textvariable=ct_var, state='readonly')
    ct_cb.grid(row=5, column=1, padx=10, pady=5)

    if default_ct in examinationAll:
        ct_cb.current(examinationAll.index(default_ct))
    elif examinationAll:
        ct_cb.current(0)

    # --- Botones ---
    btn_frame = ttk.Frame(win)
    btn_frame.grid(row=6, column=0, columnspan=2, pady=15)
    btn_frame.columnconfigure((0, 1), weight=1)

    def on_ok():
        energia = ener_var.get()
        bk = acc_var.get()
  #Para que no permita seleccionar la energía de 6FFF el los TrueBeam 3 y 4
  #      if energia == '6 FFF' and bk != 'TrueBeam1':
  #          messagebox.showerror("Error", "No se permite la energía 6 FFF en el BK3 o 4")
  #          return

        exam_name = ct_var.get()

        # --- Obtenemos el objeto Examination ---
        examination_obj = case.Examinations[exam_name] if exam_name in [ex.Name for ex in case.Examinations] else None

        # --- Obtenemos las ROIs segmentadas en esa examinación ---
        geometries = []
        if examination_obj:
            ss = case.PatientModel.StructureSets[exam_name]
            geometries = [
                geom.OfRoi.Name for geom in ss.RoiGeometries
                if geom.HasContours()  # solo las ROIs segmentadas
            ]

        # --- Guardamos todos los datos ---
        variables.update({
            "Plan": nombre_var.get(),
            "Dosimetrista": dosim_var.get(),
            "BK": bk,
            "Energia": energia,
            "Couch": couch_var.get(),
            "examinationName": exam_name,#nombre del CT seleccionado
            "_Examination": examination_obj,#objeto del CT
            "geometries": geometries
        })
        win.destroy()

    def on_cancel():
        variables.clear()
        win.destroy()

    ok_btn = ttk.Button(btn_frame, text="Ok", command=on_ok)
    ok_btn.grid(row=0, column=0, padx=10)
    cancel_btn = ttk.Button(btn_frame, text="Cancelar", command=on_cancel)
    cancel_btn.grid(row=0, column=1, padx=10)

    def key_press(event):
        if event.keysym == 'Return':
            on_ok()
        elif event.keysym == 'Escape':
            on_cancel()

    win.bind('<Key>', key_press)
    center_window(win)
    win.mainloop()

    return variables if variables else None


def ventana_ptvs():
    win = create_modal_window("Seleccionar PTVs")
    variables = {}
    ss = pm.StructureSets[datos["examinationName"]]
    PTVs_inicio = [
     geom for geom in datos["geometries"]
     if ss.RoiGeometries[geom].HasContours()
     and ss.RoiGeometries[geom].OfRoi.Type in ('Ptv', 'Ctv', 'Gtv')
 ]
    ttk.Label(win, text="Seleccione uno o más PTVs (selección múltiple con la tecla Ctrl):").pack(padx=10, pady=10)
    listbox = tk.Listbox(win, selectmode='extended', height=6)
    for item in PTVs_inicio:
        listbox.insert('end', item)
    #listbox.selection_set(0)  # seleccionamos el primero por defecto
    listbox.pack(padx=10, pady=5, fill='x')

    btn_frame = ttk.Frame(win)
    btn_frame.pack(pady=10)
    btn_frame.columnconfigure((0,1), weight=1)

    def on_ok():
        selected = [listbox.get(i) for i in listbox.curselection()]
        if not selected:
            messagebox.showerror("Error", "Por favor, seleccionar al menos un PTV")
            return
        variables['PTVs_0'] = selected
        win.destroy()

    def on_cancel():
        variables.clear()
        win.destroy()

    ok_btn = ttk.Button(btn_frame, text="Ok", command=on_ok)
    ok_btn.grid(row=0, column=0, padx=10)
    cancel_btn = ttk.Button(btn_frame, text="Cancelar", command=on_cancel)
    cancel_btn.grid(row=0, column=1, padx=10)

    def key_press(event):
        if event.keysym == 'Return':
            on_ok()
        elif event.keysym == 'Escape':
            on_cancel()

    win.bind('<Key>', key_press)

    center_window(win)
    win.mainloop()
    return variables if variables else None

def ventana_dosis_ptvs(ptvs_seleccionados):
    win = create_modal_window("Introducir las prescripciones de los PTVs")
    variables = {}

    labels = []
    entries = []

    ttk.Label(win, text="Introducir las prescripciones de los PTVs en Gy:").grid(row=0, column=0, columnspan=2, padx=10, pady=10)

    for i, ptv in enumerate(ptvs_seleccionados):
        ttk.Label(win, text=ptv + ":").grid(row=i+1, column=0, sticky='e', padx=5, pady=3)
        ent = ttk.Entry(win)
        ent.grid(row=i+1, column=1, sticky='w', padx=5, pady=3)
        ent.focus_set()
        ent.select_range(0, 'end')
        entries.append(ent)

    ttk.Label(win, text="Número de fracciones:").grid(row=len(ptvs_seleccionados)+1, column=0, sticky='e', padx=5, pady=10)
    fracciones_var = tk.StringVar()
    fracciones_entry = ttk.Entry(win, textvariable=fracciones_var)
    fracciones_entry.grid(row=len(ptvs_seleccionados)+1, column=1, sticky='w', padx=5, pady=10)
    fracciones_entry.focus()
    fracciones_entry.select_range(0, 'end')

    btn_frame = ttk.Frame(win)
    btn_frame.grid(row=len(ptvs_seleccionados)+2, column=0, columnspan=2, pady=15)
    btn_frame.columnconfigure((0,1), weight=1)

    def on_ok():
        dosis = []
        try:
            for ent in entries:
                val = float(ent.get())
                if val <= 0:
                    raise ValueError
                dosis.append(val)
            fracs = int(fracciones_var.get())
            if fracs <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Introduzca valores numéricos válidos y positivos para dosis y fracciones")
            return

        variables['Dosis_PTV_0'] = dosis
        variables['Fracciones'] = fracs
        win.destroy()

    def on_cancel():
        variables.clear()
        win.destroy()

    ok_btn = ttk.Button(btn_frame, text="Ok", command=on_ok)
    ok_btn.grid(row=0, column=0, padx=10)
    cancel_btn = ttk.Button(btn_frame, text="Cancelar", command=on_cancel)
    cancel_btn.grid(row=0, column=1, padx=10)

    def key_press(event):
        if event.keysym == 'Return':
            on_ok()
        elif event.keysym == 'Escape':
            on_cancel()

    win.bind('<Key>', key_press)
    center_window(win)
    win.mainloop()
    return variables if variables else None

def ventana_funciones_pesos():
    win = create_modal_window("Funciones y Pesos")
    variables = {}

    # Texto introductorio al inicio
    ttk.Label(win, 
              text="Introducir las funciones de optimización para los PTVs y los anillos y sus pesos correspondientes:", 
              wraplength=400,
              justify='center').grid(row=0, column=0, columnspan=3, padx=10, pady=10)

    ttk.Label(win, text="PTVs:").grid(row=1, column=0, sticky='e', padx=10, pady=5)
    funciones_ptvs_var = tk.StringVar(value=Funciones_inicio[0])
    funciones_ptvs_cb = ttk.Combobox(win, values=Funciones_inicio, textvariable=funciones_ptvs_var, state='readonly')
    funciones_ptvs_cb.grid(row=1, column=1, padx=10, pady=5)
    funciones_ptvs_cb.current(0)

    pesos_ptvs_var = tk.StringVar()
    pesos_ptvs_entry = ttk.Entry(win, textvariable=pesos_ptvs_var)
    pesos_ptvs_entry.grid(row=1, column=2, padx=10, pady=5)
    pesos_ptvs_entry.focus()
    pesos_ptvs_entry.select_range(0, 'end')

    ttk.Label(win, text="Anillos:").grid(row=2, column=0, sticky='e', padx=10, pady=5)
    funciones_anillos_var = tk.StringVar(value=Funciones_inicio[0])
    funciones_anillos_cb = ttk.Combobox(win, values=Funciones_inicio, textvariable=funciones_anillos_var, state='readonly')
    funciones_anillos_cb.grid(row=2, column=1, padx=10, pady=5)
    funciones_anillos_cb.current(1)

    pesos_anillos_var = tk.StringVar()
    pesos_anillos_entry = ttk.Entry(win, textvariable=pesos_anillos_var)
    pesos_anillos_entry.grid(row=2, column=2, padx=10, pady=5)
    pesos_anillos_entry.select_range(0, 'end')

    btn_frame = ttk.Frame(win)
    btn_frame.grid(row=3, column=0, columnspan=3, pady=15)
    btn_frame.columnconfigure((0,1), weight=1)

    def on_ok():
        try:
            pesos_ptvs = float(pesos_ptvs_var.get())
            pesos_anillos = float(pesos_anillos_var.get())
        except ValueError:
            messagebox.showerror("Error", "Introduzca pesos numéricos válidos")
            return
        variables['Funciones'] = [funciones_ptvs_var.get(), funciones_anillos_var.get()]
        variables['Pesos'] = [pesos_ptvs, pesos_anillos]
        win.destroy()

    def on_cancel():
        variables.clear()
        win.destroy()

    ok_btn = ttk.Button(btn_frame, text="Ok", command=on_ok)
    ok_btn.grid(row=0, column=0, padx=10)
    cancel_btn = ttk.Button(btn_frame, text="Cancelar", command=on_cancel)
    cancel_btn.grid(row=0, column=1, padx=10)

    def key_press(event):
        if event.keysym == 'Return':
            on_ok()
        elif event.keysym == 'Escape':
            on_cancel()

    win.bind('<Key>', key_press)
    center_window(win)
    win.mainloop()
    return variables if variables else None



def ventana_anillos():
    win = create_modal_window("Anillos")
    variables = {}

    # Texto introductorio al principio
    ttk.Label(win, 
              text="Introduce los anillos en cm y sus dosis en porcentajes sobre el total (ej. 90, 80, etc.)", 
              wraplength=400,
              justify='center').grid(row=0, column=0, columnspan=2, padx=10, pady=10)

    ttk.Label(win, text="Anillos en cm(separados por comas):").grid(row=1, column=0, sticky='w', padx=10, pady=10)
    anillos_var = tk.StringVar()
    anillos_entry = ttk.Entry(win, textvariable=anillos_var)
    anillos_entry.grid(row=1, column=1, padx=10, pady=10)
    anillos_entry.focus()
    anillos_entry.select_range(0, 'end')

    ttk.Label(win, text="Dosis para los anillos (%):").grid(row=2, column=0, sticky='w', padx=10, pady=10)
    dosis_anillos_var = tk.StringVar()
    dosis_anillos_entry = ttk.Entry(win, textvariable=dosis_anillos_var)
    dosis_anillos_entry.grid(row=2, column=1, padx=10, pady=10)

    btn_frame = ttk.Frame(win)
    btn_frame.grid(row=3, column=0, columnspan=2, pady=15)
    btn_frame.columnconfigure((0,1), weight=1)

    def on_ok():
        try:
            dosis_vals = [float(x.strip()) for x in dosis_anillos_var.get().split(',')]
        except Exception:
            messagebox.showerror("Error", "Introduzca valores numéricos válidos para dosis de anillos, separados por coma")
            return

        anillos_vals = [x.strip() for x in anillos_var.get().split(',') if x.strip()]

        # Verificación de longitud
        if len(anillos_vals) != len(dosis_vals):
            messagebox.showerror("Error", "Por favor, introduce el mismo número de anillos y dosis")
            return

        variables['Anillos'] = anillos_vals
        variables['Dosis_anillos'] = dosis_vals
        win.destroy()

    def on_cancel():
        variables.clear()
        win.destroy()

    ok_btn = ttk.Button(btn_frame, text="Ok", command=on_ok)
    ok_btn.grid(row=0, column=0, padx=10)
    cancel_btn = ttk.Button(btn_frame, text="Cancelar", command=on_cancel)
    cancel_btn.grid(row=0, column=1, padx=10)

    def key_press(event):
        if event.keysym == 'Return':
            on_ok()
        elif event.keysym == 'Escape':
            on_cancel()

    win.bind('<Key>', key_press)
    center_window(win)
    win.mainloop()
    return variables if variables else None



# Ahora, la secuencia de ejecución y asignación global

datos = {}

d = ventana_principal()
if d is None:
    print("Cancelado en ventana principal")
    exit()
datos.update(d)

d = ventana_ptvs()
if d is None:
    print("Cancelado en ventana de selección PTVs")
    exit()
datos.update(d)

d = ventana_dosis_ptvs(datos['PTVs_0'])
if d is None:
    print("Cancelado en ventana dosis PTVs")
    exit()
datos.update(d)

d = ventana_funciones_pesos()
if d is None:
    print("Cancelado en ventana funciones y pesos")
    exit()
datos.update(d)

d = ventana_anillos()
if d is None:
    print("Cancelado en ventana anillos")
    exit()
datos.update(d)

# Asignar variables globales automáticamente
for k, v in datos.items():
    globals()[k] = v

examination=case.Examinations[examinationName]
ss = pm.StructureSets[examination.Name]
OARs = [
 geom for geom in geometries
 if ss.RoiGeometries[geom].HasContours()
 and ss.RoiGeometries[geom].OfRoi.Type in ('Organ', 'Avoidance')
]
def camb_color(roi, factor):
    c = rois[roi].Color
    r = max(0, min(int(c.R * factor), 254))
    g = max(0, min(int(c.G * factor), 254))
    b = max(0, min(int(c.B * factor), 254))
    return f"{r},{g},{b}"




def create_roi_if_not_exists(nombre, color):
    try:
        case.PatientModel.CreateRoi(Name=nombre, Color=color, Type='Control', TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
    except:
        print(f'La roi ya existe')

def margin_dict(margin):
    return {'Type': 'Expand', 'Superior': margin, 'Inferior': margin,
            'Anterior': margin, 'Posterior': margin, 'Right': margin, 'Left': margin}
            
def create_algebra_geometry(nombre, source_names_a, margin_a, source_names_b, margin_b, result_operation):
 def margin_dict(margin):
     return {'Type': 'Expand', 'Superior': margin, 'Inferior': margin,
             'Anterior': margin, 'Posterior': margin, 'Right': margin, 'Left': margin}
 
 try:
  case.PatientModel.RegionsOfInterest[nombre].CreateAlgebraGeometry(
   Examination=examination,
   Algorithm="Auto",
   ExpressionA={
       'Operation': "Union",
       'SourceRoiNames': source_names_a,
       'MarginSettings': margin_dict(margin_a)
   },
   ExpressionB={
       'Operation': "Union",
       'SourceRoiNames': source_names_b,
       'MarginSettings': margin_dict(margin_b)
   },
   ResultOperation=result_operation,
   ResultMarginSettings=margin_dict(0)
  )
 
 
 except:
  print(f'La ROI "{nombre}" no se ha podido editar')
 try:
  case.PatientModel.RegionsOfInterest[nombre].CreateAlgebraGeometry(
   Examination=examination,
   Algorithm="Auto",
   ExpressionA={
   'Operation': "Union",
   'SourceRoiNames': [nombre],
   'MarginSettings': margin_dict(0)
   },
   ExpressionB={
   'Operation': "Union",
   'SourceRoiNames': [external],
   'MarginSettings': margin_dict(0)
   },
   ResultOperation='Intersection',
   ResultMarginSettings=margin_dict(0)
  )
 except:
  print('No se ha podido interseccionar con el External')

def CrearRois(nombre, roi1, roiSubs, RoiColor, margen, margen2):
    rois1 = [str(x) for x in roi1]
    rois2 = [str(x) for x in roiSubs]

    create_roi_if_not_exists(nombre, RoiColor)

    if roiSubs[0] == 'None':
        create_algebra_geometry(nombre, rois1, margen, [external], 0, "Intersection")
    else:
        create_algebra_geometry(nombre, rois1, margen, rois2, margen2, "Subtraction")
 
# ==========================
#   CREAR CLINICAL GOALS
# ==========================
def Goal(roi, prescription, vol, tipo):
    """Agregar clinical goals a un ROI."""
    try:
        plan.TreatmentCourse.EvaluationSetup.AddClinicalGoal(
            RoiName=roi,
            GoalCriteria=tipo,
            GoalType='VolumeAtDose',
            PrimaryAcceptanceLevel=vol / 100,
            ParameterValue=prescription,
            IsComparativeGoal=False,
            Priority=2147483647
        )
    except Exception as e:
        print(f"Error en el clinical goal de {roi}: {e}")
def GoalDose(roi, prescription,prescription2, vol, tipo):
    """Agregar clinical goals a un ROI."""
    try:
        plan.TreatmentCourse.EvaluationSetup.AddClinicalGoal(
            RoiName=roi,
            GoalCriteria='AtMost',
            GoalType='DoseAtVolume',
            PrimaryAcceptanceLevel=prescription,
            SecondaryAcceptanceLevel=prescription2,
            IsComparativeGoal=False,
            Priority=2147483647
        )
    except Exception as e:
        print(f"Error en el clinical goal de {roi}: {e}")

# ==============================
#   FUNCIONES DE OPTIMIZACIÓN
# ==============================
def Funcion(roi, prescription, peso, vol, tipo):
    """Agrega una función de optimización a un ROI."""
    try:
        # Número actual de funciones ya creadas
        Constit = len(plan.PlanOptimizations[0].Objective.ConstituentFunctions)
    except Exception as e:
        print("No se pudieron obtener las funciones existentes. Usando Constit=0")
        Constit = 0

    try:
        # Añadir función de optimización
        plan.PlanOptimizations[0].AddOptimizationFunction(
            FunctionType=tipo,
            RoiName=roi
        )

        # Editar parámetros de la nueva función
        dose_func = plan.PlanOptimizations[0].Objective.ConstituentFunctions[Constit].DoseFunctionParameters
        dose_func.DoseLevel = prescription
        dose_func.Weight = peso

        # Si no es UniformDose, agregar volumen
        if tipo != 'UniformDose':
            dose_func.PercentVolume = vol

    except Exception as e:
        print(f"Error en la prescripción de la ROI {roi}: {e}")


#selección de los márgenes
def set_up_treat(roi_name, margin, beam1, beam2):
    for beam in (beam1, beam2):
        beamSet.Beams[beam].SetTreatOrProtectRoi(RoiName=roi_name,TopMargin=margin, BottomMargin=margin, LeftMargin=margin, RightMargin=margin)
        
#centro de la roi en x
def roi_center_x(ss, roi):
  roi_box = ss.RoiGeometries[roi].GetBoundingBox()
  roi_x_middle = (roi_box[1].x-roi_box[0].x)/2
  roi_x = roi_box[0].x + roi_x_middle
  return roi_x


#centro de la roi en y
def roi_center_y(ss, roi):
  roi_box = ss.RoiGeometries[roi].GetBoundingBox()
  roi_y_middle = (roi_box[1].y-roi_box[0].y)/2
  roi_y = roi_box[0].y + roi_y_middle
  return roi_y  

#centro de la roi en y
def roi_center_z(ss, roi):
  roi_box = ss.RoiGeometries[roi].GetBoundingBox()
  roi_z_middle = (roi_box[1].z-roi_box[0].z)/2
  roi_z = roi_box[0].z + roi_z_middle
  return roi_z
  
# Ordenar PTVs y dosis de forma descendente
indices_ordenados = sorted(range(len(Dosis_PTV_0)), key=lambda i: Dosis_PTV_0[i], reverse=True)
PTVs = [PTVs_0[i] for i in indices_ordenados]
Dosis_PTV = [Dosis_PTV_0[i] for i in indices_ordenados]
#Rois de OARs, coge todos los Organs de clase Avoidance

OARs = [
 geom for geom in geometries
 if ss.RoiGeometries[geom].HasContours()
 and ss.RoiGeometries[geom].OfRoi.Type in ('Organ','Avoidance')
]


#Prescripcion del plan (la más alta)
MainPrescription = float(Dosis_PTV[0])
#PTV de prescripcion del plan (el de dosis más alta)
MainTarget = PTVs[0]
#limite de UM para que el índice de modulación no supere el 4
MaxArcMUVal=MainPrescription/Fracciones*150
#el nombre de BeamSet es el nombre de plan, seleccionando los primeros 16 caracteres (la longitud mxima permitida)
Beam_name=Plan[:16]
# Crear plan y beamSet
plan = case.AddNewPlan(PlanName=Plan, PlannedBy=Dosimetrista, ExaminationName=examination.Name)
beamSet = plan.AddNewBeamSet(Name=Beam_name, ExaminationName=examination.Name, MachineName=BK, \
Modality='Photons', TreatmentTechnique='VMAT', PatientPosition='HeadFirstSupine', NumberOfFractions=Fracciones, CreateSetupBeams=True)

#Default dose grid es 0.3, pero si se selecciona la energia 6FFF se baja automáticamente a 0.2 
#(porque entiendo que es una SBRT con un volumen de PTV más pequeño)
beamSet.SetDefaultDoseGrid(VoxelSize={'x': 0.3 if Energia == '6' else 0.2, 'y': 0.3 if Energia == '6' else 0.2, 'z': 0.3 if Energia == '6' else 0.2})
case.TreatmentPlans[Plan].BeamSets[Beam_name].FractionDose.UpdateDoseGridStructures()
beamSet.AddRoiPrescriptionDoseReference(RoiName=MainTarget, PrescriptionType='MedianDose', DoseValue=MainPrescription*100)

# Crear ROI principal y obtener isocentro
z_PTV='z PTV total '+str(examination.Name)
CrearRois(z_PTV, PTVs, ['None'], 'Orange', 0, 0)
isocenter = ss.RoiGeometries[z_PTV].GetCenterOfRoi()



with CompositeAction("Couches"):
 
 CouchInt=f'CouchInt{Couch}'
 ThicknessInt=None
 
 CouchSurf=f'CouchSurf{Couch}'
 ThicknessSurf=None

 if Couch=='Thin':
  ThicknessInt=4.63
  ThicknessSurf=5
  
 elif Couch=='Med':
  ThicknessInt=5.85
  ThicknessSurf=6.26
 
 elif Couch=='Thick':
  ThicknessInt=7.12
  ThicknessSurf=7.52



with CompositeAction('Introducimos couches'):
    if Couch != 'None':
        patient_db = get_current("PatientDB")
        exists = any(pm_roi.Name == CouchInt for pm_roi in pm.RegionsOfInterest)
        
        if not exists:
            templateInfo = patient_db.GetPatientModelTemplateInfo()
            for info in templateInfo:
                template = patient_db.LoadTemplatePatientModel(templateName=info['Name'], lockMode='Read')
                if template.Name == "Varian Exact IGRT couches":
                    print(template)
                    for roi_name in [CouchInt, CouchSurf]:
                        pm.CreateStructuresFromTemplate(
                            SourceTemplate=template,
                            SourceExaminationName='CT 1',
                            SourceRoiNames=[roi_name],
                            SourcePoiNames=[],
                            AssociateStructuresByName=False,
                            TargetExamination=examination,
                            InitializationOption='AlignImageCenters'
                        )

            ss = pm.StructureSets[examination.Name]
            couch_box = ss.RoiGeometries[CouchInt].GetBoundingBox()

            def translate_couch(pm, ss, examination, external, couchname):
                thickness_map = {
                    CouchSurf: ThicknessSurf,
                    CouchInt: ThicknessInt
                }
                couch_thickness = thickness_map.get(couchname, 0)
                
                ext_box = ss.RoiGeometries[external].GetBoundingBox()
                ext_center = roi_center_x(ss, external)
                PTV_center_z = roi_center_z(ss,z_PTV)
                
                if abs(ext_center) > 5:
                    ext_center = 0
                
                couch_center_x = roi_center_x(ss, couchname)
                couch_center_z = roi_center_z(ss, couchname)
                couch_box = ss.RoiGeometries[couchname].GetBoundingBox()

                y_translation = -(abs(couch_box[1].y - ext_box[1].y) - couch_thickness)
                #x_translation = ext_center - couch_center_x #lo voy a ignorar porque no me interesa que lo mueva en el eje x, 
                #se coloca bien por defecto
                z_translation = PTV_center_z - couch_center_z
                
                transMat = {
                    'M11':1.0,'M12':0.0,'M13':0.0,'M14':0,
                    'M21':0.0,'M22':1.0,'M23':0.0,'M24':y_translation,
                    'M31':0.0,'M32':0.0,'M33':1.0,'M34':z_translation,
                    'M41':0.0,'M42':0.0,'M43':0.0,'M44':1.0
                }
                pm.RegionsOfInterest[couchname].TransformROI3D(Examination=examination, TransformationMatrix=transMat)

            for couchname in [CouchSurf, CouchInt]:
                translate_couch(pm, ss, examination, external, couchname)

            ss.SimplifyContours(
                RoiNames=[external, CouchInt, CouchSurf],
                RemoveHoles3D=False, RemoveSmallContours=False, AreaThreshold=None,
                ReduceMaxNumberOfPointsInContours=False, MaxNumberOfPoints=None,
                CreateCopyOfRoi=False, ResolveOverlappingContours=True
            )
            ss.SimplifyContours(
                RoiNames=[external],
                RemoveHoles3D=True, RemoveSmallContours=False, AreaThreshold=None,
                ReduceMaxNumberOfPointsInContours=False, MaxNumberOfPoints=None,
                CreateCopyOfRoi=False, ResolveOverlappingContours=False
            )


#Scripting de DRRs "SetupBeamName"
#Angulos de mesa DRRs iniciales
CsDRR = ["0.0", "0.0", "0.0"]
#Angulos de gantry DRRs iniciales
GsDRR = ["0.0", "90.0", "270.0"]

#Vamos al beam set actual
beam_set = beamSet
#Y por cada haz vamos a adquirir su angulacion de mesa
#List con angulos de mesa del beam set
Couch3 = []
#Tomamos los valores de angulo de mesa por haz
for beam in beam_set.Beams:
    Couch3.append(str(beam.CouchRotationAngle))
#Introducimos los valores de mesa distintos de cero al list de angulos de mesa (CsDRR)
#Adjuntamos un valor gantry 0 a GsDRR por cada DRR generada por angulo de mesa
for c in Couch3:
    if c != "0.0" and CsDRR.count(c) == 0:
          CsDRR.append(c)
          GsDRR.append("0.0")
          
#Creamos un conjunto nuevo de haces de setup en base los angulos de gantry establecidos          
beam_set.UpdateSetupBeams(ResetSetupBeams=True,SetupBeamsGantryAngles=GsDRR)

#Renombramos haces de setup en base a su informacion
for i, beam in enumerate(beam_set.PatientSetup.SetupBeams):
 if (CsDRR[i] == "0.0"):
  #Nos fijamos en GsDRR y Modificamos el valor de Name y Description DRRXXX
  #name = ''
  name = str(GsDRR[i].split(".")[0])
  if len(name) == 1:
   name = "DRR00" + name
  elif len(name) == 2:
   name = "DRR0" + name
  else:
   name = "DRR" + name
 
  beam.Name = name
  beam.Description = name
  
 else:
  #Nos fijamos en CsDRR y modificamos el valor de Name y Description DRRMXXX y el valor
  #de couch rotation
  #name = str(CsDRR[i].split(".")[0])
  name = str(360 - float(CsDRR[i].split(".")[0])).split(".")[0]
  #name = (name.split(".")[0])
  
  if len(name) == 1:
   name = "DRRT00" + name
  elif len(name) == 2:
   name = "DRRT0" + name
  else:
   name = "DRRT" + name
 
  beam.Name = name
  beam.Description = name
  beam.CouchRotationAngle = float(CsDRR[i])

# Crear arcos, dos arcos completos complementarios, con el isocentro en el centro de z_PTV
beam_set.CreateArcBeam(ArcStopGantryAngle=181, \
ArcRotationDirection="CounterClockwise", BeamQualityId=Energia, \
IsocenterData={ 'Position': { 'x': isocenter.x, 'y': isocenter.y, 'z': isocenter.z}, \
'NameOfIsocenterToRef': "", 'Name': "Isocentro", 'Color': "98, 184, 234" },\
Name="G179CCW", Description="", GantryAngle=179, CouchRotationAngle=0, CouchPitchAngle=0, CouchRollAngle=0, CollimatorAngle=20)
beam_set.CopyAndReverseBeam(BeamName="G179CCW")
beam_set.Beams['G179CCW 1'].Name = "G181CW"


arco=['G179CCW','G181CW']
plan.PlanOptimizations[0].OptimizationParameters.TreatmentSetupSettings[0].BeamSettings[0].ArcConversionPropertiesPerBeam.EditArcBasedBeamOptimizationSettings(CreateDualArcs=False, FinalGantrySpacing=2, MaxArcDeliveryTime=90, BurstGantrySpacing=None, MaxArcMU=MaxArcMUVal)
plan.PlanOptimizations[0].OptimizationParameters.TreatmentSetupSettings[0].BeamSettings[1].ArcConversionPropertiesPerBeam.EditArcBasedBeamOptimizationSettings(CreateDualArcs=False, FinalGantrySpacing=2, MaxArcDeliveryTime=90, BurstGantrySpacing=None, MaxArcMU=MaxArcMUVal)




# Configurar parámetros de optimización
plan.PlanOptimizations[0].OptimizationParameters.Algorithm.MaxNumberOfIterations = 100
plan.PlanOptimizations[0].OptimizationParameters.DoseCalculation.ComputeIntermediateDose = True
plan.PlanOptimizations[0].OptimizationParameters.DoseCalculation.ComputeFinalDose = True




# Aplicar tratamientos y funciones de optimización a PTVs y anillos
oar_resta=[]
rois_restar=[]
dosis_rois_restar=[]
for j, ptv in enumerate(PTVs):
    set_up_treat(ptv, 0.5 if Energia == '6' else 0.3, arco[0], arco[1])
    func = str(Funciones[0])
    dosis=Dosis_PTV[j]
    ptv_sin=f"z {ptv} sin OARs"
    # ptv_ptv2=f'z {ptv}-PTV'
    CrearRois(ptv_sin , [ptv], ['None'], camb_color(ptv, 0.7), 0, 0.3)

    for r,dosis2 in enumerate(Dosis_PTV[:j]):
        if dosis2>dosis:
            create_algebra_geometry(ptv_sin, [ptv_sin], 0, [PTVs[r]], 0.5, "Subtraction")

    
    Funcion(ptv, dosis*95, 1, vol=95,tipo='MinDose')    

            
    for oar in OARs:
        create_algebra_geometry(ptv_sin, [ptv_sin], 0, [oar], 0, "Subtraction")
        nombre = f"z {oar} {ptv}"
        try:
            create_roi_if_not_exists(nombre, camb_color(str(ptv), 1.25))
            create_algebra_geometry(nombre, [oar], 0,[ptv] , 0, "Intersection")
            for r,dosis2 in enumerate(Dosis_PTV[:j]):
                if dosis2>dosis:
                    create_algebra_geometry(nombre, [nombre], 0, [PTVs[r]], 0, "Subtraction")
            Funcion(roi=nombre, prescription=dosis*95, peso=Pesos[0], vol=0,tipo='MinDose')
            Funcion(roi=nombre, prescription=dosis*99, peso=Pesos[0], vol=0,tipo='MaxDose')
        except:
            print(f'z {oar} {ptv} ya existe')
            
        if not ss.RoiGeometries[nombre].HasContours():
            try:
                pm.RegionsOfInterest[nombre].DeleteRoi()
            except:
                print(f'Error con z {oar} {ptv}')
        else:
            oar_resta.append(oar)

    for r,dosis2 in enumerate(Dosis_PTV[:j]):
        if dosis2>dosis:
            create_algebra_geometry(ptv_sin, [ptv_sin], 0, [PTVs[r]], 0.5, "Subtraction")

    if func == 'Min/Max DVH':
        Funcion(ptv_sin, dosis*99, peso=Pesos[0], vol=99,tipo='MinDVH')
        Funcion(ptv_sin, dosis*103, Pesos[0], vol=0.1,tipo='MaxDVH')
        
    elif func== 'Min/Max dose':
        Funcion(ptv_sin, dosis*100, Pesos[0], vol=0,tipo='MinDose')
        Funcion(ptv_sin, dosis*100, Pesos[0], vol=0,tipo='MaxDose')
        
    Goal(ptv, dosis*95, vol=95,tipo='AtLeast')
    GoalDose(ptv, prescription=dosis*105, prescription2=dosis*107,vol=0,tipo='AtMost')
            
    for i in range(0,len(Anillos)):
        anillo = f'z anillo {ptv} {Anillos[i]} cm'
        rois_restar.append(anillo)
        margen2 = Anillos[i - 1] if i > 0 else 0

        create_roi_if_not_exists(anillo, camb_color(ptv, 0.4))
        create_algebra_geometry(anillo, [ptv], Anillos[i], [ptv], margen2, "Subtraction")
                
        dosis_anillo = Dosis_anillos[i] * dosis
        dosis_rois_restar.append(dosis_anillo)
        func_anillo = str(Funciones[1])
        if func_anillo == 'Min/Max DVH':
            Funcion(roi=anillo, prescription=dosis_anillo, peso=Pesos[1], vol=0.1,tipo='MaxDVH')
        elif func_anillo == 'Min/Max dose':
            Funcion(roi=anillo,prescription=dosis_anillo, peso=Pesos[1], vol=0,tipo='MaxDose')

        for g,ptv_r in enumerate(PTVs):
            dosis_ptv=Dosis_PTV[g]
            create_algebra_geometry(anillo, [anillo], 0, [ptv_r], 0, "Subtraction")
            for i,porc in enumerate(Dosis_anillos):
                if dosis_ptv*porc>dosis_anillo:
                    create_algebra_geometry(anillo, [anillo], 0, [ptv_r], Anillos[i], "Subtraction")

  
for oar in oar_resta:
 nombre2 = f"y {oar}"
 create_roi_if_not_exists(nombre2, camb_color(oar, 0.7))
 create_algebra_geometry(nombre2, [oar], 0, [z_PTV], 0.3, "Subtraction") 



beamSet.SetDefaultDoseGrid(VoxelSize={'x': 0.3 if Energia == '6' else 0.2, 'y': 0.3 if Energia == '6' else 0.2, 'z': 0.3 if Energia == '6' else 0.2})
    
def aviso_final():
    mensaje = (
        'Plan terminado. Compruebe el ángulo de colimador y las funciones.\n\n'
        'Las intersecciones de los OARs con los respectivos PTVs se llaman "z (órgano) (PTV)".\n\n'
        f'Los OARs sin los PTVs se llaman "y (órgano)" y la suma de todos los PTVs se llama "{z_PTV}".'
    )
    root = tk.Tk()
    root.withdraw()  # Oculta la ventana principal
    messagebox.showinfo("Aviso Final", mensaje)
    root.destroy() 
aviso_final()
