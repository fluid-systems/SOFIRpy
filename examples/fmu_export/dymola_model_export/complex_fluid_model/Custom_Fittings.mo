within ;
package Custom_Fittings
  model CurvedBend_Cutom "Curved bend flow model"
    extends Modelica.Fluid.Dissipation.Utilities.Icons.PressureLoss.Bend_i;
    extends Modelica.Fluid.Interfaces.PartialPressureLoss;

    parameter Modelica.Fluid.Fittings.BaseClasses.Bends.CurvedBend.Geometry geometry
      "Geometry of curved bend"
        annotation (Placement(transformation(extent={{-20,0},{0,20}})));

        Real zeta "Widerstandsbeiwert";
        constant Real pi=2*Modelica.Math.asin(1.0);

  protected
    parameter Medium.AbsolutePressure dp_small(min=0)=
               Modelica.Fluid.Dissipation.PressureLoss.Bend.dp_curvedOverall_DP(
                  geometry,
                  Modelica.Fluid.Dissipation.PressureLoss.Bend.dp_curvedOverall_IN_var(
                    rho=Medium.density(state_dp_small),
                    eta=Medium.dynamicViscosity(state_dp_small)),
                  m_flow_small)
      "Default small pressure drop for regularization of laminar and zero flow (calculated from m_flow_small)";

  equation
    if allowFlowReversal then
       m_flow = Modelica.Fluid.Fittings.BaseClasses.Bends.CurvedBend.massFlowRate(
                  dp, geometry, d_a, d_b, eta_a, eta_b, dp_small, m_flow_small);
    else
       m_flow = Modelica.Fluid.Dissipation.PressureLoss.Bend.dp_curvedOverall_MFLOW(
                  geometry,
                  Modelica.Fluid.Dissipation.PressureLoss.Bend.dp_curvedOverall_IN_var(rho=d_a, eta=eta_a), dp);
    end if;

    zeta = dp*2 / d_a / ((V_flow/(geometry.d_hyd^2/4* pi))^2);

    annotation (Documentation(info="<html>
<p>
This component models a <b>curved bend</b> in the overall flow regime for incompressible and single-phase fluid flow through circular cross sectional area considering surface roughness. It is expected that also compressible fluid flow can be handled up to about Ma = 0.3. It is assumed that neither mass nor energy is stored in this component.
In the model basically a function is called to compute the mass flow rate as a function
of pressure loss for a curved bend. Also the inverse of this function is defined, and a tool
might use this inverse function instead, in order to avoid the solution of a nonlinear equation.
</p>

<p>
The details of the model are described in the
<a href=\"modelica://Modelica.Fluid.Dissipation.Utilities.SharedDocumentation.PressureLoss.Bend.dp_curvedOverall\">documentation of the underlying function</a>.
</p>
</html>"));
  end CurvedBend_Cutom;
  annotation (uses(Modelica(version="3.2.2")));
end Custom_Fittings;
