model DC_Motor
  Modelica.Electrical.Analog.Basic.Ground ground annotation (
    Placement(visible = true, transformation(origin={-98,34},    extent = {{-10, -10}, {10, 10}}, rotation = 270)));
  Modelica.Mechanics.Rotational.Sources.Torque torque annotation (
    Placement(visible = true, transformation(origin = {60, -20}, extent = {{10, -10}, {-10, 10}}, rotation = 0)));
  Modelica.Mechanics.Rotational.Components.Damper damper(d = 0.1, phi_rel(displayUnit = "rad"))  annotation (
    Placement(visible = true, transformation(origin = {20, -48}, extent = {{-10, -10}, {10, 10}}, rotation = 90)));
  Modelica.Mechanics.Rotational.Components.Fixed fixed annotation (
    Placement(visible = true, transformation(origin = {20, -76}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  Modelica.Electrical.Machines.BasicMachines.DCMachines.DC_PermanentMagnet dC_PermanentMagnet(IaNominal = dcpmData.IaNominal, Jr = dcpmData.Jr, Js = dcpmData.Js, La = dcpmData.La, Ra = dcpmData.Ra, TaNominal = dcpmData.TaNominal, TaOperational = 293.15, TaRef = dcpmData.TaRef, VaNominal = dcpmData.VaNominal, alpha20a = dcpmData.alpha20a, brushParameters = dcpmData.brushParameters, coreParameters = dcpmData.coreParameters, frictionParameters = dcpmData.frictionParameters, ia(fixed = true), phiMechanical(fixed = true), strayLoadParameters = dcpmData.strayLoadParameters, useSupport = false, wMechanical(fixed = true), wNominal = dcpmData.wNominal) annotation (
    Placement(visible = true, transformation(origin = {-60, -20}, extent = {{-20, -20}, {20, 20}}, rotation = 0)));
  parameter Modelica.Electrical.Machines.Utilities.ParameterRecords.DcPermanentMagnetData dcpmData annotation (
    Placement(visible = true, transformation(extent = {{-60, -88}, {-40, -68}}, rotation = 0)));
  Modelica.Mechanics.Rotational.Components.Inertia inertia(J = 0.5) annotation (
    Placement(visible = true, transformation(origin = {1, -19}, extent = {{-19, -19}, {19, 19}}, rotation = 0)));
  Modelica.Mechanics.Rotational.Sensors.SpeedSensor speedSensor annotation (
    Placement(visible = true, transformation(origin={-30,30},    extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  Modelica.Electrical.Analog.Sources.SignalVoltage V_in annotation (
    Placement(visible = true, transformation(origin = {-60, 34}, extent = {{12, -12}, {-12, 12}}, rotation = 0)));
  Modelica.Blocks.Sources.Step setp(height = -250, startTime = 5)  annotation (
    Placement(visible = true, transformation(origin = {96, -20}, extent = {{10, -10}, {-10, 10}}, rotation = 0)));
  Modelica.Mechanics.Rotational.Sensors.TorqueSensor MotorTorque
    annotation (Placement(transformation(extent={{-36,-4},{-16,16}})));
  Modelica.Blocks.Interfaces.RealInput u
    annotation (Placement(transformation(extent={{-140,40},{-100,80}})));
  Modelica.Blocks.Interfaces.RealOutput y
    annotation (Placement(transformation(extent={{98,24},{128,54}})));
equation
  connect(damper.flange_a, fixed.flange) annotation (
    Line(points = {{20, -58}, {20, -76}}));
  connect(inertia.flange_b, damper.flange_b) annotation (
    Line(points = {{20, -19}, {20, -38}}));
  connect(speedSensor.flange, dC_PermanentMagnet.flange) annotation (
    Line(points={{-40,30},{-40,-20}}));
  connect(dC_PermanentMagnet.pin_an, V_in.n) annotation (
    Line(points = {{-72, 0}, {-72, 34}}, color = {0, 0, 255}));
  connect(dC_PermanentMagnet.pin_ap, V_in.p) annotation (
    Line(points = {{-48, 0}, {-48, 34}}, color = {0, 0, 255}));
  connect(ground.p, V_in.n) annotation (
    Line(points={{-88,34},{-72,34}},      color = {0, 0, 255}));
  connect(torque.flange, inertia.flange_b) annotation (
    Line(points = {{50, -20}, {35, -20}, {35, -19}, {20, -19}}));
  connect(torque.tau, setp.y) annotation (
    Line(points = {{72, -20}, {85, -20}}, color = {0, 0, 127}));
  connect(MotorTorque.flange_a, dC_PermanentMagnet.flange)
    annotation (Line(points={{-36,6},{-36,-20},{-40,-20}}, color={0,0,0}));
  connect(MotorTorque.flange_b, inertia.flange_a)
    annotation (Line(points={{-16,6},{-18,6},{-18,-19}}, color={0,0,0}));
  connect(V_in.v, u)
    annotation (Line(points={{-60,42.4},{-60,60},{-120,60}}, color={0,0,127}));
  connect(speedSensor.w, y) annotation (Line(points={{-19,30},{42,30},{42,39},{
          113,39}}, color={0,0,127}));
  connect(y, y) annotation (Line(points={{113,39},{109.5,39},{109.5,39},{113,39}},
        color={0,0,127}));
  annotation (
    uses(Modelica(version="3.2.2")));
end DC_Motor;
