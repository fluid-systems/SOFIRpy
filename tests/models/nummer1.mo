within ;
model nummer1
  Modelica.Electrical.Analog.Basic.Resistor resistor(R=5)
    annotation (Placement(transformation(extent={{-18,26},{2,46}})));
  Modelica.Electrical.Analog.Basic.Ground ground
    annotation (Placement(transformation(extent={{50,-32},{70,-12}})));
  Modelica.Electrical.Analog.Basic.Inductor inductor(L= 0.001)
    annotation (Placement(transformation(extent={{30,26},{50,46}})));
  Modelica.Electrical.Analog.Basic.Capacitor capacitor(C= 0.005)
    annotation (Placement(transformation(extent={{28,-12},{48,8}})));
  Modelica.Electrical.Analog.Sources.SignalVoltage signalVoltage annotation (
      Placement(transformation(
        extent={{-10,-10},{10,10}},
        rotation=90,
        origin={-38,8})));
  Modelica.Blocks.Interfaces.RealInput u_in annotation (
    Placement(visible = true, transformation(extent = {{-110, 0}, {-70, 40}}, rotation = 0), iconTransformation(extent = {{-110, -12}, {-70, 28}}, rotation = 0)));
  Modelica.Electrical.Analog.Sensors.CurrentSensor currentSensor annotation (
    Placement(visible = true, transformation(origin = {-10, -2}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  Modelica.Blocks.Interfaces.RealOutput y_out annotation (
    Placement(visible = true, transformation(origin = {-68, -16}, extent = {{-10, -10}, {10, 10}}, rotation = 0), iconTransformation(origin = {-6, -30}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  Modelica.Blocks.Interfaces.RealInput u_in2 annotation (
    Placement(visible = true, transformation(origin = {-82, -44}, extent = {{-20, -20}, {20, 20}}, rotation = 0), iconTransformation(origin = {-72, -48}, extent = {{-20, -20}, {20, 20}}, rotation = 0)));
  Modelica.Blocks.Math.Gain gain(k = 3)  annotation (
    Placement(visible = true, transformation(origin = {-14, -44}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
equation
  connect(resistor.n, inductor.p) annotation (
    Line(points = {{2, 36}, {30, 36}}, color = {0, 0, 255}));
  connect(inductor.n, capacitor.n) annotation (
    Line(points = {{50, 36}, {60, 36}, {60, -2}, {48, -2}}, color = {0, 0, 255}));
  connect(ground.p, capacitor.n) annotation (
    Line(points = {{60, -12}, {60, -2}, {48, -2}}, color = {0, 0, 255}));
  connect(resistor.p, signalVoltage.n) annotation (
    Line(points = {{-18, 36}, {-38, 36}, {-38, 18}}, color = {0, 0, 255}));
  connect(signalVoltage.v, u_in) annotation (
    Line(points={{-45,8},{-90,8},{-90,20}},        color = {0, 0, 127}));
  connect(currentSensor.p, signalVoltage.p) annotation (
    Line(points = {{-20, -2}, {-38, -2}}, color = {0, 0, 255}));
  connect(currentSensor.n, capacitor.p) annotation (
    Line(points = {{0, -2}, {28, -2}}, color = {0, 0, 255}));
  connect(currentSensor.i, y_out) annotation (
    Line(points = {{-10, -12}, {-10, -16}, {-68, -16}}, color = {0, 0, 127}));
  connect(u_in2, gain.u) annotation (
    Line(points = {{-82, -44}, {-26, -44}}, color = {0, 0, 127}));
  annotation (
    Icon(coordinateSystem(preserveAspectRatio=false)),
    Diagram(coordinateSystem(preserveAspectRatio=false)),
    uses(Modelica(version="3.2.2")));
end nummer1;
