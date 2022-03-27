Warning: The HiFi Truss_P6 print is one of the most difficult prints in the entire project. It also is one of the most important structural pieces in the model. Removing the support material has a HIGH likelihood of breaking the primary structural load paths. This print is very challenging. 

I've uploaded the 3mf file to include the support blockers I used to ensure that the internal support was not too tricky. When removing the support, start at the bottom. Removing the top support material is the most challenging part, and try not to twist the print when removing suport. 

My print settings used for this piece are below: (these are tuned to my printer of course, might not work for yours)

Settings:

	Quality
	Layer Height: 0.12 mm
	Initial Layer Height: 0.12 mm
	Line Width: 0.4 mm
  
	Walls
	Wall Line Count: 4
  
	Top/Bottom
	Top Thickness: 0.84 mm
	Bottom Thickness: 0.84 mm

	Infill
	Infill Density: 20%
	Infill Pattern: cubic

	Material
	Printing Temperature: 200°C
	Build Plate Temperature: 75°C

	Speed
	Print Speed: 50 mm/s

	Cooling
	Enable Print Cooling: True
	Fan Speed: 100%

	Support
	Generate Support: True
	Support Structure: normal
	Tree Support Branch Angle: 30 °
	Tree Support Branch Distance: 1 mm
	Tree Support Branch Diameter: 2 mm
	Tree Support Branch Diameter Angle: 3 °
	Tree Support Collision Resolution: 0.2 mm
	Support Placement: everywhere
	Support Overhang Angle: 60 °

	Build Plate Adhesion
	Build Plate Adhesion Type: brim
