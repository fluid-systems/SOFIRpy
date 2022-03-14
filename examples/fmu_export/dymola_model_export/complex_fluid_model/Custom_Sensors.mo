within ;
package Custom_Sensors
  model VolumeFlowRate_nonSI
    "Ideal sensor for volume flow rate in m^3/h"
    extends Modelica.Fluid.Sensors.BaseClasses.PartialFlowSensor;
    extends Modelica.Icons.RotationalSensor;
    Modelica.Blocks.Interfaces.RealOutput V_flow(final quantity="VolumeFlowRate",
                                                 final unit="m3/h")
      "Volume flow rate from port_a to port_b"
      annotation (Placement(transformation(
          origin={0,110},
          extent={{10,-10},{-10,10}},
          rotation=270)));

  protected
    Medium.Density rho_a_inflow "Density of inflowing fluid at port_a";
    Medium.Density rho_b_inflow
      "Density of inflowing fluid at port_b or rho_a_inflow, if uni-directional flow";
    Medium.Density d "Density of the passing fluid";
  equation
    if allowFlowReversal then
       rho_a_inflow = Medium.density(Medium.setState_phX(port_b.p, port_b.h_outflow, port_b.Xi_outflow));
       rho_b_inflow = Medium.density(Medium.setState_phX(port_a.p, port_a.h_outflow, port_a.Xi_outflow));
       d = Modelica.Fluid.Utilities.regStep(port_a.m_flow, rho_a_inflow, rho_b_inflow, m_flow_small);
    else
       d = Medium.density(Medium.setState_phX(port_b.p, port_b.h_outflow, port_b.Xi_outflow));
       rho_a_inflow = d;
       rho_b_inflow = d;
    end if;
    V_flow = port_a.m_flow/d*60*60;
  annotation (
    Icon(coordinateSystem(preserveAspectRatio=false, extent={{-100,-100},{100,
              100}}), graphics={
          Text(
            extent={{160,120},{0,90}},
            lineColor={0,0,0},
            textString="V_flow"),
          Line(points={{0,100},{0,70}}, color={0,0,127}),
          Line(points={{-100,0},{-70,0}}, color={0,128,255}),
          Line(points={{70,0},{100,0}}, color={0,128,255})}),
    Documentation(info="<html>
<p>
This component monitors the volume flow rate flowing from port_a to port_b.
The sensor is ideal, i.e., it does not influence the fluid.
</p>
</html>"));
  end VolumeFlowRate_nonSI;

  model getZeta "Zeta-Sensor"
    extends Modelica.Fluid.Sensors.BaseClasses.PartialRelativeSensor;
    extends Modelica.Fluid.Sensors.BaseClasses.PartialFlowSensor;
    extends Modelica.Icons.RotationalSensor;

    Real zeta "Dimensionsloser Widerstandsbeiwert";
    Real p_rel(final quantity="Pressure",       final unit="Pa",
                                                displayUnit="bar");
    Real V_flow(final quantity="VolumeFlowRate", final unit="m3/s");
    Real u(unit="m3/s");

    constant Modelica.Constants.pi pi;

    parameter Real d_hyd(unit="m");
  protected
    Medium.Density rho_a_inflow "Density of inflowing fluid at port_a";
    Medium.Density rho_b_inflow
      "Density of inflowing fluid at port_b or rho_a_inflow, if uni-directional flow";
    Medium.Density d "Density of the passing fluid";
  equation
    if allowFlowReversal then
       rho_a_inflow = Medium.density(Medium.setState_phX(port_b.p, port_b.h_outflow, port_b.Xi_outflow));
       rho_b_inflow = Medium.density(Medium.setState_phX(port_a.p, port_a.h_outflow, port_a.Xi_outflow));
       d = Modelica.Fluid.Utilities.regStep(port_a.m_flow, rho_a_inflow, rho_b_inflow, m_flow_small);
    else
       d = Medium.density(Medium.setState_phX(port_b.p, port_b.h_outflow, port_b.Xi_outflow));
       rho_a_inflow = d;
       rho_b_inflow = d;
    end if;
    V_flow = port_a.m_flow/d;

    u = V_flow / (pi* d_hyd^2 / 4);
    p_rel = port_b.p - port_a.p;
    zeta = p_rel * 2 / d / u^2;




    annotation (
      Icon(graphics={
          Line(points={{0,-30},{0,-80}}, color={0,0,127}),
          Text(
            extent={{130,-70},{4,-100}},
            lineColor={0,0,0},
            textString="p_rel")}),
      Documentation(info="<html>
<p>
The relative pressure \"port_a.p - port_b.p\" is determined between
the two ports of this component and is provided as output signal. The
sensor should be connected in parallel with other equipment, no flow
through the sensor is allowed.
</p>
</html>"));
  end getZeta;

  model VolumeFlowRate_test "Ideal sensor for volume flow rate"
    extends Modelica.Fluid.Sensors.BaseClasses.PartialFlowSensor;
    extends Modelica.Icons.RotationalSensor;
    Real V_flow(final quantity="VolumeFlowRate", final unit="m3/s")
      "Volume flow rate from port_a to port_b"
      annotation (Placement(transformation(
          origin={0,110},
          extent={{10,-10},{-10,10}},
          rotation=270)));

  protected
    Medium.Density rho_a_inflow "Density of inflowing fluid at port_a";
    Medium.Density rho_b_inflow
      "Density of inflowing fluid at port_b or rho_a_inflow, if uni-directional flow";
    Medium.Density d "Density of the passing fluid";
  equation
    if allowFlowReversal then
       rho_a_inflow = Medium.density(Medium.setState_phX(port_b.p, port_b.h_outflow, port_b.Xi_outflow));
       rho_b_inflow = Medium.density(Medium.setState_phX(port_a.p, port_a.h_outflow, port_a.Xi_outflow));
       d = Modelica.Fluid.Utilities.regStep(port_a.m_flow, rho_a_inflow, rho_b_inflow, m_flow_small);
    else
       d = Medium.density(Medium.setState_phX(port_b.p, port_b.h_outflow, port_b.Xi_outflow));
       rho_a_inflow = d;
       rho_b_inflow = d;
    end if;
    V_flow = port_a.m_flow/d;
  annotation (
    Icon(coordinateSystem(preserveAspectRatio=false, extent={{-100,-100},{100,
              100}}), graphics={
          Text(
            extent={{160,120},{0,90}},
            lineColor={0,0,0},
            textString="V_flow"),
          Line(points={{0,100},{0,70}}, color={0,0,127}),
          Line(points={{-100,0},{-70,0}}, color={0,128,255}),
          Line(points={{70,0},{100,0}}, color={0,128,255})}),
    Documentation(info="<html>
<p>
This component monitors the volume flow rate flowing from port_a to port_b.
The sensor is ideal, i.e., it does not influence the fluid.
</p>
</html>"));
  end VolumeFlowRate_test;
  annotation (uses(Modelica(version="3.2.2")));
end Custom_Sensors;
