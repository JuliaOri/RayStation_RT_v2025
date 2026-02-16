from raystation import *
from tkinter import simpledialog
import numpy as np
import tkinter as tk
from tkinter import messagebox
import sys

case = get_current('Case')
examination = get_current('Examination')
plan=get_current('Plan')

pm = case.PatientModel
rois = pm.RegionsOfInterest
ss = pm.StructureSets[examination.Name]
z_PTV='z PTV total '+str(examination.Name)
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


class InputWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ingresar datos")
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

        tk.Label(self, text="Dosis:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        tk.Label(self, text="Distancia:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        tk.Label(self, text="Peso:").grid(row=2, column=0, sticky="e", padx=5, pady=5)

        self.entry_Dosis = tk.Entry(self)
        self.entry_Distancia = tk.Entry(self)
        self.entry_Peso = tk.Entry(self)

        self.entry_Dosis.grid(row=0, column=1, padx=5, pady=5)
        self.entry_Dosis.focus()

        self.entry_Distancia.grid(row=1, column=1, padx=5, pady=5)
        self.entry_Peso.grid(row=2, column=1, padx=5, pady=5)

        btn_frame = tk.Frame(self)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)

        btn_ok = tk.Button(btn_frame, text="OK", command=self.on_ok)
        btn_ok.pack(side="left", padx=10)

        btn_cancel = tk.Button(btn_frame, text="Cancelar", command=self.on_cancel)
        btn_cancel.pack(side="left", padx=10)

        self.bind('<Return>', lambda event: self.on_ok())
        self.bind('<Escape>', lambda event: self.on_cancel())

        self.Dosis = None
        self.Distancia = None
        self.Peso = None

        self.centrar_ventana()

    def centrar_ventana(self):
        self.update_idletasks()
        ancho_ventana = self.winfo_width()
        alto_ventana = self.winfo_height()
        ancho_pantalla = self.winfo_screenwidth()
        alto_pantalla = self.winfo_screenheight()

        x = (ancho_pantalla // 2) - (ancho_ventana // 2)
        y = (alto_pantalla // 2) - (alto_ventana // 2)

        self.geometry(f'+{x}+{y}')

    def on_ok(self):
        try:
            dosis = float(self.entry_Dosis.get())
            distancia = float(self.entry_Distancia.get())
            peso = float(self.entry_Peso.get())
        except ValueError:
            messagebox.showerror("Error", "Por favor ingresa valores numéricos válidos.")
            return

        self.Dosis = dosis
        self.Distancia = distancia
        self.Peso = peso
        self.destroy()

    def on_cancel(self):
        sys.exit()

def main():
    app = InputWindow()
    app.mainloop()
    return app.Dosis, app.Distancia, app.Peso

if __name__ == "__main__":
    Dosis, Distancia, Peso = main()
    print("Dosis:", Dosis)
    print("Distancia:", Distancia)
    print("Peso:", Peso)


def intentar_crear(numero):
    base = f"z{numero}"
    intento = 0
    while True:
        if intento == 0:
            nombre = base
        else:
            nombre = f"{base} {intento}"
        try:
            roi = pm.CreateRoi(Name=nombre, Type='Control', Color='White')
            roi.CreateRoiGeometryFromDose(DoseDistribution=plan.TreatmentCourse.TotalDose, ThresholdLevel=Dosis*100)
            print(f"Creado con nombre: '{nombre}'")
            return nombre  # Devuelve el nombre que funcionó
        except Exception as e:
            # Si da error, probar siguiente
            intento += 1


nombre=intentar_crear(Dosis)
try:
	a = plan.PlanOptimizations[0].Objective.ConstituentFunctions._
	a=a.split()
	afin=a[-1]
	afin=np.float(afin.replace('_',''))+1
	constit=int(afin)
	print(a,afin)
except:
	constit = 0


try:
    Funcion(nombre, Dosis*100, Peso, 0, 'MaxDose')
except:
	print('vaya')
	

	

try:
    create_algebra_geometry(nombre, [nombre], 0, [z_PTV], float(Distancia), 'Subtraction')
    


except:
	print(f'La ROI "{nombre}" no se ha podido editar')