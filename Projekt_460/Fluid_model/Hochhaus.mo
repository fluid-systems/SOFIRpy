within ;
model Hochhaus "Parallelschaltung, nur Stockwerke 1, 3 und 5"

  replaceable package Medium =
      Modelica.Media.Water.ConstantPropertyLiquidWater;

  Modelica.Fluid.Sources.FixedBoundary SOURCE(nPorts=1,
    redeclare package Medium = Medium,
    use_p=true,
    use_T=true,
    T=system.T_ambient,
    p=106000)                                           annotation (Placement(
        transformation(
        extent={{-10,-10},{10,10}},
        rotation=180,
        origin={232,-288})));

  Modelica.Fluid.Pipes.StaticPipe R1(
    redeclare package Medium = Medium,
    isCircular=true,
    height_ab=0,
    length=35e-2,
    roughness=20e-6,
    diameter=45.2e-3)
                    annotation (Placement(transformation(
        extent={{-4,-6},{4,6}},
        rotation=180,
        origin={206,-288})));

  Modelica.Fluid.Pipes.StaticPipe R4(
    redeclare package Medium = Medium,
    isCircular=true,
    roughness=7e-6,
    height_ab=-0.115,
    length=0.115,
    diameter=45.2e-3)
                  annotation (Placement(transformation(
        extent={{-5,-6},{5,6}},
        rotation=270,
        origin={110,-299})));

  Modelica.Fluid.Pipes.StaticPipe R5(
    redeclare package Medium = Medium,
    isCircular=true,
    height_ab=0,
    roughness=7e-6,
    diameter=45.2e-3,
    length=0.3)     annotation (Placement(transformation(
        extent={{-7,-6},{7,6}},
        rotation=180,
        origin={89,-310})));

  Custom_Pump_V2.BaseClasses_Custom.Pump_vs GF80_2(
    redeclare package Medium = Medium,
    m_flow_start=0.24,
    redeclare function flowCharacteristic =
        Custom_Pump.BaseClasses_Custom.PumpCharacteristics.quadraticFlow (c={-0.065158,
            0.34196,8.1602}),
    redeclare function powerCharacteristic =
        Custom_Pump.BaseClasses_Custom.PumpCharacteristics.cubicPower (c={-0.14637,
            1.1881,23.0824,53.0304,6.0431}),
    rpm_rel=0.93969,
    use_N_in=true,
    V=0.1,
    use_HeatTransfer=true,
    redeclare model HeatTransfer =
        Modelica.Fluid.Vessels.BaseClasses.HeatTransfer.IdealHeatTransfer)
                   annotation (Placement(transformation(
        extent={{-12,-12},{12,12}},
        rotation=90,
        origin={-34,-156})));

  Modelica.Fluid.Pipes.StaticPipe R14(
    redeclare package Medium = Medium,
    isCircular=true,
    diameter=20e-3,
    roughness=7e-6,
    length=0.3,
    height_ab=0.3) annotation (Placement(transformation(
        extent={{-10,-10},{10,10}},
        rotation=90,
        origin={26,78})));

Real P_ges(unit="W") "Gesamtleistung";
Real eta_ges "Gesamtwirkungsgrad";
Real head_ges(unit="m") "Gesamtfoerderhoehe";

  inner Modelica.Fluid.System system(
    g=9.81,
    p_ambient=99000,
    T_ambient=293.15)
    annotation (Placement(transformation(extent={{260,-360},{280,-340}})));

  Modelica.Fluid.Pipes.StaticPipe R16(
    redeclare package Medium = Medium,
    isCircular=true,
    diameter=20e-3,
    roughness=7e-6,
    length=2.3,
    height_ab=2.3) annotation (Placement(transformation(
        extent={{-10,-10},{10,10}},
        rotation=90,
        origin={-72,82})));

  Modelica.Fluid.Pipes.StaticPipe R17(
    redeclare package Medium = Medium,
    isCircular=true,
    diameter=20e-3,
    roughness=7e-6,
    length=4.3,
    height_ab=4.3) annotation (Placement(transformation(
        extent={{-10,-10},{10,10}},
        rotation=90,
        origin={-240,84})));

  Custom_Sensors.VolumeFlowRate_nonSI Q_ges(redeclare package Medium =
        Medium) annotation (Placement(
        transformation(
        extent={{-15,14},{15,-14}},
        rotation=180,
        origin={63,-310})));
  Modelica.Fluid.Pipes.StaticPipe R3(
    redeclare package Medium = Medium,
    isCircular=true,
    height_ab=0,
    length=0.5,
    roughness=7e-6,
    diameter=45.2e-3)
                    annotation (Placement(transformation(
        extent={{-8,-6},{8,6}},
        rotation=180,
        origin={134,-288})));

  Modelica.Fluid.Pipes.StaticPipe R2(
    redeclare package Medium = Medium,
    isCircular=true,
    height_ab=0,
    length=12.5e-2,
    roughness=7e-6,
    diameter=45.2e-3)
                    annotation (Placement(transformation(
        extent={{-4,-6},{4,6}},
        rotation=180,
        origin={174,-288})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice T1_1(
    redeclare package Medium = Medium,
    use_zeta=true,
    diameter=20e-3,
    zeta=1.4) annotation (Placement(transformation(
        extent={{-5,-6},{5,6}},
        rotation=90,
        origin={42,-305})));

  Modelica.Fluid.Fittings.AbruptAdaptor V2(
    redeclare package Medium = Medium,
    diameter_a=20e-3,
    diameter_b=25e-3) annotation (Placement(transformation(
        extent={{-6,-6},{6,6}},
        rotation=90,
        origin={-34,-194})));

  Modelica.Fluid.Fittings.AbruptAdaptor V4(
    redeclare package Medium = Medium,
    diameter_a=25e-3,
    diameter_b=20e-3) annotation (Placement(transformation(
        extent={{-6,-8},{6,8}},
        rotation=90,
        origin={-34,-132})));

  Modelica.Fluid.Fittings.AbruptAdaptor V1(
    redeclare package Medium = Medium,
    diameter_a=20e-3,
    diameter_b=25e-3) annotation (Placement(transformation(
        extent={{-6,-6},{6,6}},
        rotation=90,
        origin={42,-194})));

  Modelica.Fluid.Fittings.AbruptAdaptor V3(
    redeclare package Medium = Medium,
    diameter_a=25e-3,
    diameter_b=20e-3) annotation (Placement(transformation(
        extent={{-6,-8},{6,8}},
        rotation=90,
        origin={42,-132})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice T5S(
    redeclare package Medium = Medium,
    use_zeta=true,
    diameter=20e-3,
    zeta=1.9) annotation (Placement(transformation(
        extent={{-10,-10},{10,10}},
        rotation=90,
        origin={-72,30})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice T4S(
    redeclare package Medium = Medium,
    use_zeta=true,
    diameter=20e-3,
    zeta=1.9) annotation (Placement(transformation(
        extent={{-10,-10},{10,10}},
        rotation=90,
        origin={26,30})));

  Modelica.Fluid.Fittings.Bends.CurvedBend B2(redeclare package Medium =
        Medium, geometry(
      R_0=62e-3,
      d_hyd=45.2e-3,
      delta=1.5707963267949,
      K=7e-9)) annotation (Placement(transformation(
        extent={{-5,-6},{5,6}},
        rotation=180,
        origin={157,-288})));
  Modelica.Fluid.Fittings.Bends.CurvedBend B3(redeclare package Medium =
        Medium, geometry(
      R_0=62e-3,
      d_hyd=45.2e-3,
      delta=1.5707963267949,
      K=7e-9)) annotation (Placement(transformation(
        extent={{-5,-6},{5,6}},
        rotation=180,
        origin={117,-288})));
  Modelica.Fluid.Fittings.Bends.CurvedBend B4(redeclare package Medium =
        Medium, geometry(
      R_0=62e-3,
      d_hyd=45.2e-3,
      delta=1.5707963267949,
      K=7e-9)) annotation (Placement(transformation(
        extent={{-5,6},{5,-6}},
        rotation=180,
        origin={105,-310})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice H1(
    redeclare package Medium = Medium,
    diameter=20e-3,
    use_zeta=true,
    zeta=0.3) annotation (Placement(transformation(
        extent={{-5,-6},{5,6}},
        rotation=90,
        origin={42,-281})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice E4(
    redeclare package Medium = Medium,
    use_zeta=true,
    diameter=20e-3,
    zeta=1.8) annotation (Placement(transformation(
        extent={{-10,-10},{10,10}},
        rotation=90,
        origin={-240,30})));

  Modelica.Fluid.Pipes.StaticPipe D_H2(
    redeclare package Medium = Medium,
    isCircular=true,
    length=0.18,
    height_ab=0.18,
    roughness=0,
    diameter=25e-3)
                 annotation (Placement(transformation(
        extent={{-6,-6},{6,6}},
        rotation=90,
        origin={-34,-178})));

  Modelica.Fluid.Pipes.StaticPipe D_H1(
    redeclare package Medium = Medium,
    isCircular=true,
    length=0.18,
    height_ab=0.18,
    roughness=0,
    diameter=25e-3) annotation (Placement(transformation(
        extent={{-6,-8},{6,8}},
        rotation=90,
        origin={42,-178})));

  Custom_Fittings.CurvedBend_Cutom B1(
               redeclare package Medium =
        Medium, geometry(
      R_0=62e-3,
      d_hyd=45.2e-3,
      delta=1.5707963267949,
      K=7e-9))                                            annotation (Placement(
        transformation(
        extent={{-5,-6},{5,6}},
        rotation=180,
        origin={191,-288})));

  Custom_Pump_V2.BaseClasses_Custom.Pump_vs
                                         GF80_1(
    redeclare package Medium = Medium,
    m_flow_start=0.24,
    redeclare function flowCharacteristic =
        Custom_Pump.BaseClasses_Custom.PumpCharacteristics.quadraticFlow (c={-0.065158,
            0.34196,8.1602}),
    redeclare function powerCharacteristic =
        Custom_Pump.BaseClasses_Custom.PumpCharacteristics.cubicPower (c={-0.14637,
            1.1881,23.0824,53.0304,6.0431}),
    rpm_rel=0.93969,
    use_N_in=true,
    V=0.1,
    use_HeatTransfer=true,
    redeclare model HeatTransfer =
        Modelica.Fluid.Vessels.BaseClasses.HeatTransfer.IdealHeatTransfer)
                     annotation (Placement(transformation(
        extent={{-12,-12},{12,12}},
        rotation=90,
        origin={42,-156})));

  Modelica.Fluid.Pipes.StaticPipe R7(
    redeclare package Medium = Medium,
    isCircular=true,
    diameter=20e-3,
    roughness=7e-6,
    length=0.34,
    height_ab=0.34) annotation (Placement(transformation(
        extent={{-7,-8},{7,8}},
        rotation=90,
        origin={42,-257})));

  Modelica.Fluid.Pipes.StaticPipe R8(
    redeclare package Medium = Medium,
    isCircular=true,
    diameter=20e-3,
    roughness=7e-6,
    length=0.34,
    height_ab=0.34) annotation (Placement(transformation(
        extent={{-7,-8},{7,8}},
        rotation=90,
        origin={-34,-257})));

  Modelica.Fluid.Pipes.StaticPipe D_A2(
    redeclare package Medium = Medium,
    isCircular=true,
    diameter=20e-3,
    roughness=1e-5,
    length=0.135,
    height_ab=0.135) annotation (Placement(transformation(
        extent={{-6,-6},{6,6}},
        rotation=90,
        origin={-34,-212})));

  Modelica.Fluid.Pipes.StaticPipe D_A1(
    redeclare package Medium = Medium,
    isCircular=true,
    diameter=20e-3,
    roughness=1e-5,
    length=0.135,
    height_ab=0.135) annotation (Placement(transformation(
        extent={{-6,-6},{6,6}},
        rotation=90,
        origin={42,-212})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice U2(
    redeclare package Medium = Medium,
    diameter=20e-3,
    use_zeta=true,
    zeta=0.4) annotation (Placement(transformation(
        extent={{-5,-6},{5,6}},
        rotation=90,
        origin={-34,-229})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice U1(
    redeclare package Medium = Medium,
    diameter=20e-3,
    use_zeta=true,
    zeta=0.4) annotation (Placement(transformation(
        extent={{-5,-6},{5,6}},
        rotation=90,
        origin={42,-227})));

  Modelica.Fluid.Pipes.StaticPipe D_B2(
    redeclare package Medium = Medium,
    isCircular=true,
    diameter=20e-3,
    roughness=1e-5,
    length=0.2,
    height_ab=0.2)  annotation (Placement(transformation(
        extent={{-5,-8},{5,8}},
        rotation=90,
        origin={-34,-117})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice H4(
    redeclare package Medium = Medium,
    diameter=20e-3,
    use_zeta=true,
    zeta=0.4) annotation (Placement(transformation(
        extent={{-6,-8},{6,8}},
        rotation=90,
        origin={-34,-102})));

  Modelica.Fluid.Pipes.StaticPipe D_B1(
    redeclare package Medium = Medium,
    isCircular=true,
    diameter=20e-3,
    roughness=1e-5,
    length=0.2,
    height_ab=0.2)  annotation (Placement(transformation(
        extent={{-5,-8},{5,8}},
        rotation=90,
        origin={42,-117})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice H3(
    redeclare package Medium = Medium,
    diameter=20e-3,
    use_zeta=true,
    zeta=0.4) annotation (Placement(transformation(
        extent={{-6,-8},{6,8}},
        rotation=90,
        origin={42,-102})));

  Modelica.Fluid.Pipes.StaticPipe R10(
    redeclare package Medium = Medium,
    isCircular=true,
    diameter=20e-3,
    roughness=7e-6,
    length=0.50,
    height_ab=0.50) annotation (Placement(transformation(
        extent={{-10,-10},{10,10}},
        rotation=90,
        origin={-34,-80})));

  Modelica.Fluid.Pipes.StaticPipe R9(
    redeclare package Medium = Medium,
    isCircular=true,
    diameter=20e-3,
    roughness=7e-6,
    length=0.50,
    height_ab=0.50) annotation (Placement(transformation(
        extent={{-10,-10},{10,10}},
        rotation=90,
        origin={42,-80})));

  Modelica.Fluid.Sources.FixedBoundary SINK(
    redeclare package Medium = Medium,
    use_p=true,
    use_T=true,
    T=system.T_ambient,
    p=99000,
    nPorts=3)
             annotation (Placement(transformation(
        extent={{-10,-10},{10,10}},
        rotation=180,
        origin={284,146})));

  Modelica.Fluid.Pipes.StaticPipe H5_R(
    redeclare package Medium = Medium,
    isCircular=true,
    diameter=20e-3,
    height_ab=0,
    length=0.195,
    roughness=0) annotation (Placement(transformation(
        extent={{-7,-10},{7,10}},
        rotation=0,
        origin={137,146})));

  Custom_Sensors.VolumeFlowRate_nonSI Q_floor1(redeclare package Medium =
        Medium)
    annotation (Placement(transformation(extent={{150,156},{170,136}})));

  Custom_Sensors.VolumeFlowRate_nonSI Q_floor3(redeclare package Medium =
        Medium)
    annotation (Placement(transformation(extent={{-10,10},{10,-10}},
        rotation=0,
        origin={160,226})));
  Modelica.Fluid.Valves.ValveIncompressible Valve_floor3(
    redeclare package Medium = Medium,
    filteredOpening=false,
    CvData=Modelica.Fluid.Types.CvTypes.Kv,
    m_flow_nominal=1,
    Kv=29.5,
    dp_nominal=100000,
    redeclare function valveCharacteristic =
        Modelica.Fluid.Valves.BaseClasses.ValveCharacteristics.equalPercentage)
    annotation (Placement(transformation(extent={{180,216},{200,236}})));

  Custom_Sensors.VolumeFlowRate_nonSI Q_floor5(redeclare package Medium =
        Medium)
    annotation (Placement(transformation(extent={{-10,10},{10,-10}},
        rotation=0,
        origin={160,308})));
  Modelica.Fluid.Valves.ValveIncompressible Valve_floor5(
    redeclare package Medium = Medium,
    filteredOpening=false,
    CvData=Modelica.Fluid.Types.CvTypes.Kv,
    m_flow_nominal=1,
    Kv=29.5,
    dp_nominal=100000,
    redeclare function valveCharacteristic =
        Modelica.Fluid.Valves.BaseClasses.ValveCharacteristics.equalPercentage)
    annotation (Placement(transformation(extent={{180,298},{200,318}})));

  Modelica.Fluid.Valves.ValveIncompressible Valve_floor1(
    redeclare package Medium = Medium,
    CvData=Modelica.Fluid.Types.CvTypes.Kv,
    filteredOpening=false,
    m_flow_nominal=1,
    Kv=29.5,
    dp_nominal=100000,
    redeclare function valveCharacteristic =
        Modelica.Fluid.Valves.BaseClasses.ValveCharacteristics.equalPercentage)
    annotation (Placement(transformation(extent={{174,136},{194,156}})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice K1(
    redeclare package Medium = Medium,
    diameter=20e-3,
    use_zeta=true,
    zeta=0.4) annotation (Placement(transformation(
        extent={{-10,-10},{10,10}},
        rotation=0,
        origin={76,146})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice E5(
    redeclare package Medium = Medium,
    use_zeta=true,
    diameter=20e-3,
    zeta=1.8) annotation (Placement(transformation(
        extent={{-10,-10},{10,10}},
        rotation=90,
        origin={-240,298})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice E3(
    redeclare package Medium = Medium,
    use_zeta=true,
    diameter=20e-3,
    zeta=1.8) annotation (Placement(transformation(
        extent={{-10,-10},{10,10}},
        rotation=90,
        origin={-72,216})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice E2(
    redeclare package Medium = Medium,
    use_zeta=true,
    diameter=20e-3,
    zeta=1.8) annotation (Placement(transformation(
        extent={{-10,-10},{10,10}},
        rotation=90,
        origin={26,136})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice H5(
    redeclare package Medium = Medium,
    diameter=20e-3,
    use_zeta=true,
    zeta=0.3) annotation (Placement(transformation(
        extent={{-10,-10},{10,10}},
        rotation=0,
        origin={116,146})));

  Modelica.Fluid.Pipes.StaticPipe s1(
    redeclare package Medium = Medium,
    isCircular=true,
    diameter=20e-3,
    height_ab=0,
    roughness=7e-6,
    length=0.115) annotation (Placement(transformation(
        extent={{-7,-10},{7,10}},
        rotation=0,
        origin={39,146})));

  Modelica.Fluid.Pipes.StaticPipe K1_R(
    redeclare package Medium = Medium,
    isCircular=true,
    diameter=20e-3,
    height_ab=0,
    length=0.1,
    roughness=0) annotation (Placement(transformation(
        extent={{-7,-10},{7,10}},
        rotation=0,
        origin={55,146})));

  Modelica.Fluid.Pipes.StaticPipe QS1(
    redeclare package Medium = Medium,
    isCircular=true,
    diameter=20e-3,
    height_ab=0,
    length=0.155,
    roughness=1e-5) annotation (Placement(transformation(
        extent={{-7,-10},{7,10}},
        rotation=0,
        origin={97,146})));

  Modelica.Fluid.Pipes.StaticPipe K2_R(
    redeclare package Medium = Medium,
    isCircular=true,
    diameter=20e-3,
    height_ab=0,
    roughness=7e-6,
    length=0.5)     annotation (Placement(transformation(
        extent={{-7,-10},{7,10}},
        rotation=0,
        origin={233,146})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice K2(
    redeclare package Medium = Medium,
    diameter=20e-3,
    use_zeta=true,
    zeta=0.4) annotation (Placement(transformation(
        extent={{-10,-10},{10,10}},
        rotation=0,
        origin={210,146})));

  Modelica.Fluid.Pipes.StaticPipe H6_R(
    redeclare package Medium = Medium,
    isCircular=true,
    diameter=20e-3,
    height_ab=0,
    length=0.195,
    roughness=0) annotation (Placement(transformation(
        extent={{-7,-10},{7,10}},
        rotation=0,
        origin={139,226})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice K3(
    redeclare package Medium = Medium,
    diameter=20e-3,
    use_zeta=true,
    zeta=0.4) annotation (Placement(transformation(
        extent={{-10,-10},{10,10}},
        rotation=0,
        origin={78,226})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice H6(
    redeclare package Medium = Medium,
    diameter=20e-3,
    use_zeta=true,
    zeta=0.3) annotation (Placement(transformation(
        extent={{-10,-10},{10,10}},
        rotation=0,
        origin={118,226})));

  Modelica.Fluid.Pipes.StaticPipe s2(
    redeclare package Medium = Medium,
    isCircular=true,
    diameter=20e-3,
    height_ab=0,
    roughness=7e-6,
    length=0.915) annotation (Placement(transformation(
        extent={{-7,-10},{7,10}},
        rotation=0,
        origin={41,226})));

  Modelica.Fluid.Pipes.StaticPipe K3_R(
    redeclare package Medium = Medium,
    isCircular=true,
    diameter=20e-3,
    height_ab=0,
    length=0.1,
    roughness=0) annotation (Placement(transformation(
        extent={{-7,-10},{7,10}},
        rotation=0,
        origin={57,226})));

  Modelica.Fluid.Pipes.StaticPipe QS2(
    redeclare package Medium = Medium,
    isCircular=true,
    diameter=20e-3,
    height_ab=0,
    length=0.155,
    roughness=1e-5) annotation (Placement(transformation(
        extent={{-7,-10},{7,10}},
        rotation=0,
        origin={99,226})));

  Modelica.Fluid.Pipes.StaticPipe H7_R(
    redeclare package Medium = Medium,
    isCircular=true,
    diameter=20e-3,
    height_ab=0,
    length=0.195,
    roughness=0) annotation (Placement(transformation(
        extent={{-7,-10},{7,10}},
        rotation=0,
        origin={139,308})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice K5(
    redeclare package Medium = Medium,
    diameter=20e-3,
    use_zeta=true,
    zeta=0.4) annotation (Placement(transformation(
        extent={{-10,-10},{10,10}},
        rotation=0,
        origin={78,308})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice H7(
    redeclare package Medium = Medium,
    diameter=20e-3,
    use_zeta=true,
    zeta=0.3) annotation (Placement(transformation(
        extent={{-10,-10},{10,10}},
        rotation=0,
        origin={118,308})));

  Modelica.Fluid.Pipes.StaticPipe s3(
    redeclare package Medium = Medium,
    isCircular=true,
    diameter=20e-3,
    height_ab=0,
    roughness=7e-6,
    length=1.715) annotation (Placement(transformation(
        extent={{-7,-10},{7,10}},
        rotation=0,
        origin={41,308})));

  Modelica.Fluid.Pipes.StaticPipe K5_R(
    redeclare package Medium = Medium,
    isCircular=true,
    diameter=20e-3,
    height_ab=0,
    length=0.1,
    roughness=0) annotation (Placement(transformation(
        extent={{-7,-10},{7,10}},
        rotation=0,
        origin={57,308})));

  Modelica.Fluid.Pipes.StaticPipe QS3(
    redeclare package Medium = Medium,
    isCircular=true,
    diameter=20e-3,
    height_ab=0,
    length=0.155,
    roughness=1e-5) annotation (Placement(transformation(
        extent={{-7,-10},{7,10}},
        rotation=0,
        origin={99,308})));

  Modelica.Fluid.Pipes.StaticPipe K4_R(
    redeclare package Medium = Medium,
    isCircular=true,
    diameter=20e-3,
    height_ab=0,
    roughness=7e-6,
    length=0.5) annotation (Placement(transformation(
        extent={{-7,-10},{7,10}},
        rotation=0,
        origin={237,226})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice K4(
    redeclare package Medium = Medium,
    diameter=20e-3,
    use_zeta=true,
    zeta=0.4) annotation (Placement(transformation(
        extent={{-10,-10},{10,10}},
        rotation=0,
        origin={216,226})));

  Modelica.Fluid.Pipes.StaticPipe K6_R(
    redeclare package Medium = Medium,
    isCircular=true,
    diameter=20e-3,
    height_ab=0,
    roughness=7e-6,
    length=0.5) annotation (Placement(transformation(
        extent={{-7,-10},{7,10}},
        rotation=0,
        origin={235,308})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice K6(
    redeclare package Medium = Medium,
    diameter=20e-3,
    use_zeta=true,
    zeta=0.4) annotation (Placement(transformation(
        extent={{-10,-10},{10,10}},
        rotation=0,
        origin={214,308})));

  Modelica.Fluid.Pipes.StaticPipe R15(
    redeclare package Medium = Medium,
    isCircular=true,
    diameter=20e-3,
    height_ab=0,
    roughness=7e-6,
    length=80e-2) annotation (Placement(transformation(
        extent={{11,-8},{-11,8}},
        rotation=0,
        origin={-43,2})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice T4D(
    redeclare package Medium = Medium,
    diameter=20e-3,
    zeta=0.3) annotation (Placement(transformation(extent={{8,-6},{-8,10}})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice T3_1(
    diameter=20e-3,
    redeclare package Medium = Medium,
    zeta=0.5) annotation (Placement(transformation(
        extent={{-8,-8},{8,8}},
        rotation=90,
        origin={42,-58})));

  Modelica.Fluid.Pipes.StaticPipe R6(
    length=0.2,
    diameter=45.2e-3,
    redeclare package Medium = Medium,
    roughness=7e-6)
    annotation (Placement(transformation(extent={{6,-316},{-14,-304}})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice T1_2(
    redeclare package Medium = Medium,
    diameter=45.2e-3,
    zeta=0.2)
    annotation (Placement(transformation(extent={{26,-316},{14,-304}})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice T2(
    redeclare package Medium = Medium,
    use_zeta=true,
    diameter=20e-3,
    zeta=1.4) annotation (Placement(transformation(
        extent={{-5,-6},{5,6}},
        rotation=90,
        origin={-34,-305})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice H2(
    redeclare package Medium = Medium,
    diameter=20e-3,
    use_zeta=true,
    zeta=0.3) annotation (Placement(transformation(
        extent={{-5,-6},{5,6}},
        rotation=90,
        origin={-34,-279})));

  Custom_Pump_V2.BaseClasses_Custom.Pump_vs YONOS(
    redeclare package Medium = Medium,
    use_N_in=true,
    redeclare function flowCharacteristic =
        Custom_Pump_V2.BaseClasses_Custom.PumpCharacteristics.quadraticFlow (c=
            {-0.31462,0.36629,5.0907}),
    redeclare function powerCharacteristic =
        Custom_Pump_V2.BaseClasses_Custom.PumpCharacteristics.cubicPower (c={-0.32719,
            0.36765,16.4571,16.2571,3.5722}),
    V=0.1,
    use_HeatTransfer=true,
    redeclare model HeatTransfer =
        Modelica.Fluid.Vessels.BaseClasses.HeatTransfer.IdealHeatTransfer)
    annotation (Placement(transformation(extent={{-164,-8},{-184,12}})));

  Modelica.Fluid.Pipes.StaticPipe R11(
    redeclare package Medium = Medium,
    length=0.2,
    diameter=20e-3,
    roughness=7e-6)
    annotation (Placement(transformation(extent={{-12,-70},{8,-52}})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice HB1(
    zeta=0.3,
    redeclare package Medium = Medium,
    diameter=20e-3)
    annotation (Placement(transformation(extent={{-34,-70},{-18,-54}})));

  Modelica.Fluid.Pipes.StaticPipe R12(
    redeclare package Medium = Medium,
    diameter=20e-3,
    roughness=7e-6,
    length=0.19,
    height_ab=0.19) annotation (Placement(transformation(
        extent={{-7,-8},{7,8}},
        rotation=90,
        origin={42,-35})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice HB2(
    zeta=0.3,
    redeclare package Medium = Medium,
    diameter=20e-3) annotation (Placement(transformation(
        extent={{-8,-8},{8,8}},
        rotation=90,
        origin={42,-16})));

  Modelica.Fluid.Pipes.StaticPipe R13(
    redeclare package Medium = Medium,
    length=0.1,
    diameter=20e-3,
    roughness=7e-6)
    annotation (Placement(transformation(extent={{40,-6},{30,10}})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice T5D(
    redeclare package Medium = Medium,
    use_zeta=true,
    diameter=20e-3,
    zeta=0.3) annotation (Placement(transformation(
        extent={{-10,-10},{10,10}},
        rotation=180,
        origin={-90,2})));

  Modelica.Fluid.Pipes.StaticPipe D_H3(
    redeclare package Medium = Medium,
    isCircular=true,
    length=0.18,
    roughness=0,
    diameter=25e-3,
    height_ab=0) annotation (Placement(transformation(
        extent={{-6,-10},{6,10}},
        rotation=180,
        origin={-156,2})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice U3(
    redeclare package Medium = Medium,
    diameter=20e-3,
    use_zeta=true,
    zeta=0.4) annotation (Placement(transformation(
        extent={{-7,8},{7,-8}},
        rotation=180,
        origin={-113,2})));

  Modelica.Fluid.Pipes.StaticPipe D_A3(
    redeclare package Medium = Medium,
    isCircular=true,
    diameter=20e-3,
    roughness=1e-5,
    length=0.135,
    height_ab=0) annotation (Placement(transformation(
        extent={{-6,-6},{6,6}},
        rotation=180,
        origin={-128,2})));

  Modelica.Fluid.Fittings.AbruptAdaptor V5(
    redeclare package Medium = Medium,
    diameter_a=20e-3,
    diameter_b=25e-3) annotation (Placement(transformation(
        extent={{-6,-8},{6,8}},
        rotation=180,
        origin={-142,2})));

  Modelica.Fluid.Fittings.AbruptAdaptor V6(
    redeclare package Medium = Medium,
    diameter_a=25e-3,
    diameter_b=20e-3) annotation (Placement(transformation(
        extent={{-6,-8},{6,8}},
        rotation=180,
        origin={-194,2})));

  Modelica.Fluid.Pipes.StaticPipe D_B3(
    redeclare package Medium = Medium,
    isCircular=true,
    diameter=20e-3,
    roughness=1e-5,
    height_ab=0,
    length=0.485)   annotation (Placement(transformation(
        extent={{-6,-8},{6,8}},
        rotation=180,
        origin={-228,2})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice U4(
    redeclare package Medium = Medium,
    diameter=20e-3,
    use_zeta=true,
    zeta=0.4) annotation (Placement(transformation(
        extent={{-6,-8},{6,8}},
        rotation=180,
        origin={-212,2})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice C1(
    redeclare package Medium = Medium,
    diameter=20e-3,
    zeta=1) annotation (Placement(transformation(extent={{246,136},{266,156}})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice C2(
    diameter=20e-3,
    zeta=1,
    redeclare package Medium = Medium)
    annotation (Placement(transformation(extent={{248,216},{268,236}})));
  Modelica.Fluid.Fittings.SimpleGenericOrifice C3(
    redeclare package Medium = Medium,
    diameter=20e-3,
    zeta=1) annotation (Placement(transformation(extent={{246,298},{266,318}})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice T3_2(
    redeclare package Medium = Medium,
    diameter=20e-3,
    zeta=0.75)
    annotation (Placement(transformation(extent={{12,-70},{32,-50}})));

  Modelica.Blocks.Interfaces.RealInput u_v_5
    annotation (Placement(transformation(extent={{-320,310},{-280,350}})));
  Modelica.Blocks.Interfaces.RealInput u_v_3
    annotation (Placement(transformation(extent={{-320,230},{-280,270}})));
  Modelica.Blocks.Interfaces.RealInput u_v_1
    annotation (Placement(transformation(extent={{-320,150},{-280,190}})));
  Modelica.Blocks.Interfaces.RealInput u_p_2
    annotation (Placement(transformation(extent={{-320,34},{-280,74}})));
  Modelica.Blocks.Interfaces.RealInput u_p_1
    annotation (Placement(transformation(extent={{-318,-170},{-278,-130}})));
  Modelica.Blocks.Interfaces.RealOutput y_v_5
    annotation (Placement(transformation(extent={{300,266},{328,294}})));
  Modelica.Blocks.Interfaces.RealOutput y_v_3
    annotation (Placement(transformation(extent={{300,186},{328,214}})));
  Modelica.Blocks.Interfaces.RealOutput y_v_1
    annotation (Placement(transformation(extent={{300,106},{328,134}})));
  Modelica.Blocks.Interfaces.RealOutput y_p_2
    annotation (Placement(transformation(extent={{300,-62},{328,-34}})));
  Modelica.Blocks.Interfaces.RealOutput y_p_1
    annotation (Placement(transformation(extent={{300,-160},{328,-132}})));
  Modelica.Fluid.Sensors.Pressure pressure(redeclare package Medium =
        Medium)
    annotation (Placement(transformation(extent={{60,-144},{80,-124}})));
  Modelica.Fluid.Sensors.Pressure pressure1(redeclare package Medium =
        Medium)
    annotation (Placement(transformation(extent={{60,-168},{80,-148}})));
  Modelica.Fluid.Sensors.Pressure pressure2(redeclare package Medium =
        Medium) annotation (Placement(
        transformation(
        extent={{-7,-7},{7,7}},
        rotation=270,
        origin={-177,-17})));
  Modelica.Blocks.Math.Add add(k1=1, k2=-1)
    annotation (Placement(transformation(extent={{96,-156},{116,-136}})));
  Modelica.Fluid.Sensors.Pressure pressure3(redeclare package Medium =
        Medium) annotation (Placement(
        transformation(
        extent={{-7,-7},{7,7}},
        rotation=270,
        origin={-157,-17})));
  Modelica.Blocks.Math.Add add1(k1=-1) annotation (Placement(transformation(
        extent={{-6,-6},{6,6}},
        rotation=270,
        origin={-166,-38})));
  Modelica.Fluid.Fittings.SimpleGenericOrifice H8(
    redeclare package Medium = Medium,
    use_zeta=true,
    diameter=20e-4,
    zeta=1000)
              annotation (Placement(transformation(
        extent={{-6,-8},{6,8}},
        rotation=180,
        origin={-68,-58})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice H9(
    redeclare package Medium = Medium,
    use_zeta=true,
    diameter=20e-4,
    zeta=1000)
              annotation (Placement(transformation(
        extent={{-6,-8},{6,8}},
        rotation=180,
        origin={4,-114})));

  Modelica.Fluid.Fittings.SimpleGenericOrifice H10(
    redeclare package Medium = Medium,
    use_zeta=true,
    diameter=20e-4,
    zeta=1000)
              annotation (Placement(transformation(
        extent={{-6,-8},{6,8}},
        rotation=0,
        origin={-160,-70})));

  Modelica.Fluid.Sources.FixedBoundary SINK1(
    redeclare package Medium = Medium,
    use_p=true,
    use_T=true,
    T=system.T_ambient,
    p=99000,
    nPorts=3)
             annotation (Placement(transformation(
        extent={{-10,-10},{10,10}},
        rotation=0,
        origin={-110,-108})));

equation
  connect(SOURCE.ports[1], R1.port_a)
    annotation (Line(points={{222,-288},{210,-288}}, color={0,127,255}));
    P_ges =GF80_2.W_total + GF80_1.W_total;
    eta_ges =(GF80_2.dp_pump*GF80_2.V_flow + GF80_1.dp_pump*GF80_1.V_flow)/
    P_ges;
    head_ges =GF80_2.head + GF80_1.head;

  connect(T4S.port_b, R14.port_a)
    annotation (Line(points={{26,40},{26,68}}, color={0,127,255}));
  connect(R2.port_b, B2.port_a)
    annotation (Line(points={{170,-288},{162,-288}}, color={0,127,255}));
  connect(B2.port_b, R3.port_a)
    annotation (Line(points={{152,-288},{142,-288}}, color={0,127,255}));
  connect(R3.port_b, B3.port_a)
    annotation (Line(points={{126,-288},{122,-288}}, color={0,127,255}));
  connect(R4.port_a, B3.port_b)
    annotation (Line(points={{110,-294},{110,-288},{112,-288}},
                                                     color={0,127,255}));
  connect(R4.port_b, B4.port_a)
    annotation (Line(points={{110,-304},{110,-310}}, color={0,127,255}));
  connect(B4.port_b, R5.port_a)
    annotation (Line(points={{100,-310},{96,-310}},color={0,127,255}));
  connect(T5S.port_b, R16.port_a)
    annotation (Line(points={{-72,40},{-72,72}}, color={0,127,255}));
  connect(E4.port_b, R17.port_a)
    annotation (Line(points={{-240,40},{-240,74}}, color={0,127,255}));
  connect(V2.port_b, D_H2.port_a)
    annotation (Line(points={{-34,-188},{-34,-184}}, color={0,127,255}));
  connect(R1.port_b, B1.port_a)
    annotation (Line(points={{202,-288},{196,-288}}, color={0,127,255}));
  connect(R2.port_a, B1.port_b)
    annotation (Line(points={{178,-288},{186,-288}}, color={0,127,255}));
  connect(D_H2.port_b, GF80_2.port_a)
    annotation (Line(points={{-34,-172},{-34,-168}}, color={0,127,255}));
  connect(V1.port_b, D_H1.port_a)
    annotation (Line(points={{42,-188},{42,-184}}, color={0,127,255}));
  connect(GF80_2.port_b, V4.port_a)
    annotation (Line(points={{-34,-144},{-34,-138}}, color={0,127,255}));
  connect(D_H1.port_b, GF80_1.port_a)
    annotation (Line(points={{42,-172},{42,-168}}, color={0,127,255}));
  connect(V3.port_a, GF80_1.port_b)
    annotation (Line(points={{42,-138},{42,-144}}, color={0,127,255}));
  connect(R5.port_b, Q_ges.port_a)
    annotation (Line(points={{82,-310},{78,-310}}, color={0,127,255}));
  connect(Q_ges.port_b, T1_1.port_a)
    annotation (Line(points={{48,-310},{42,-310}}, color={0,127,255}));
  connect(T1_1.port_b, H1.port_a)
    annotation (Line(points={{42,-300},{42,-286}}, color={0,127,255}));
  connect(V2.port_a, D_A2.port_b)
    annotation (Line(points={{-34,-200},{-34,-206}}, color={0,127,255}));
  connect(V1.port_a,D_A1. port_b)
    annotation (Line(points={{42,-200},{42,-206}},   color={0,127,255}));
  connect(R8.port_b, U2.port_a)
    annotation (Line(points={{-34,-250},{-34,-234}}, color={0,127,255}));
  connect(D_A2.port_a, U2.port_b)
    annotation (Line(points={{-34,-218},{-34,-224}}, color={0,127,255}));
  connect(R7.port_b, U1.port_a)
    annotation (Line(points={{42,-250},{42,-232}}, color={0,127,255}));
  connect(D_A1.port_a,U1. port_b)
    annotation (Line(points={{42,-218},{42,-222}},   color={0,127,255}));
  connect(D_B2.port_b, H4.port_a)
    annotation (Line(points={{-34,-112},{-34,-108}}, color={0,127,255}));
  connect(V4.port_b, D_B2.port_a)
    annotation (Line(points={{-34,-126},{-34,-122}}, color={0,127,255}));
  connect(D_B1.port_b, H3.port_a)
    annotation (Line(points={{42,-112},{42,-108}}, color={0,127,255}));
  connect(V3.port_b, D_B1.port_a)
    annotation (Line(points={{42,-126},{42,-122}}, color={0,127,255}));
  connect(H4.port_b, R10.port_a)
    annotation (Line(points={{-34,-96},{-34,-90}}, color={0,127,255}));
  connect(H3.port_b, R9.port_a)
    annotation (Line(points={{42,-96},{42,-90}}, color={0,127,255}));
  connect(H5_R.port_b,Q_floor1. port_a)
    annotation (Line(points={{144,146},{150,146}}, color={0,127,255}));
  connect(R17.port_b, E5.port_a)
    annotation (Line(points={{-240,94},{-240,288}}, color={0,127,255}));
  connect(R16.port_b, E3.port_a)
    annotation (Line(points={{-72,92},{-72,206}}, color={0,127,255}));
  connect(R14.port_b, E2.port_a)
    annotation (Line(points={{26,88},{26,126}}, color={0,127,255}));
  connect(Q_floor5.port_b,Valve_floor5. port_a)
    annotation (Line(points={{170,308},{180,308}}, color={0,127,255}));
  connect(Q_floor3.port_b,Valve_floor3. port_a)
    annotation (Line(points={{170,226},{180,226}}, color={0,127,255}));
  connect(Q_floor1.port_b,Valve_floor1. port_a)
    annotation (Line(points={{170,146},{174,146}}, color={0,127,255}));
  connect(H5_R.port_a,H5. port_b)
    annotation (Line(points={{130,146},{126,146}}, color={0,127,255}));
  connect(E2.port_b,s1. port_a)
    annotation (Line(points={{26,146},{32,146}}, color={0,127,255}));
  connect(H5.port_a,QS1. port_b)
    annotation (Line(points={{106,146},{104,146}}, color={0,127,255}));
  connect(s1.port_b,K1_R. port_a)
    annotation (Line(points={{46,146},{48,146}}, color={0,127,255}));
  connect(QS1.port_a,K1. port_b)
    annotation (Line(points={{90,146},{86,146}}, color={0,127,255}));
  connect(K1_R.port_b,K1. port_a)
    annotation (Line(points={{62,146},{66,146}}, color={0,127,255}));
  connect(K2_R.port_a,K2. port_b) annotation (Line(points={{226,146},{220,146}},
                                color={0,127,255}));
  connect(Valve_floor1.port_b,K2. port_a) annotation (Line(points={{194,146},{
          200,146}},                     color={0,127,255}));
  connect(H6_R.port_a, H6.port_b)
    annotation (Line(points={{132,226},{128,226}}, color={0,127,255}));
  connect(H6.port_a,QS2. port_b)
    annotation (Line(points={{108,226},{106,226}}, color={0,127,255}));
  connect(s2.port_b, K3_R.port_a)
    annotation (Line(points={{48,226},{50,226}}, color={0,127,255}));
  connect(QS2.port_a,K3. port_b)
    annotation (Line(points={{92,226},{88,226}}, color={0,127,255}));
  connect(K3_R.port_b, K3.port_a)
    annotation (Line(points={{64,226},{68,226}}, color={0,127,255}));
  connect(H7_R.port_a, H7.port_b)
    annotation (Line(points={{132,308},{128,308}}, color={0,127,255}));
  connect(H7.port_a, QS3.port_b)
    annotation (Line(points={{108,308},{106,308}}, color={0,127,255}));
  connect(s3.port_b, K5_R.port_a)
    annotation (Line(points={{48,308},{50,308}}, color={0,127,255}));
  connect(QS3.port_a,K5. port_b)
    annotation (Line(points={{92,308},{88,308}}, color={0,127,255}));
  connect(K5_R.port_b, K5.port_a)
    annotation (Line(points={{64,308},{68,308}}, color={0,127,255}));
  connect(E3.port_b, s2.port_a)
    annotation (Line(points={{-72,226},{34,226}},  color={0,127,255}));
  connect(E5.port_b,s3. port_a)
    annotation (Line(points={{-240,308},{34,308}}, color={0,127,255}));
  connect(K4_R.port_a, K4.port_b)
    annotation (Line(points={{230,226},{226,226}}, color={0,127,255}));
  connect(K6_R.port_a, K6.port_b)
    annotation (Line(points={{228,308},{224,308}}, color={0,127,255}));
  connect(Valve_floor5.port_b, K6.port_a)
    annotation (Line(points={{200,308},{204,308}}, color={0,127,255}));
  connect(Valve_floor3.port_b,K4. port_a)
    annotation (Line(points={{200,226},{206,226}}, color={0,127,255}));
  connect(H6_R.port_b, Q_floor3.port_a)
    annotation (Line(points={{146,226},{150,226}}, color={0,127,255}));
  connect(H7_R.port_b, Q_floor5.port_a)
    annotation (Line(points={{146,308},{150,308}}, color={0,127,255}));
  connect(R9.port_b, T3_1.port_a)
    annotation (Line(points={{42,-70},{42,-66}}, color={0,127,255}));
  connect(T4D.port_b, R15.port_a)
    annotation (Line(points={{-8,2},{-32,2}}, color={0,127,255}));
  connect(T1_1.port_a, T1_2.port_a)
    annotation (Line(points={{42,-310},{26,-310}}, color={0,127,255}));
  connect(R6.port_a, T1_2.port_b)
    annotation (Line(points={{6,-310},{14,-310}}, color={0,127,255}));
  connect(R6.port_b, T2.port_a)
    annotation (Line(points={{-14,-310},{-34,-310}}, color={0,127,255}));
  connect(T2.port_b, H2.port_a)
    annotation (Line(points={{-34,-300},{-34,-284}}, color={0,127,255}));
  connect(R11.port_a, HB1.port_b) annotation (Line(points={{-12,-61},{-18,-61},
          {-18,-62}}, color={0,127,255}));
  connect(R10.port_b, HB1.port_a)
    annotation (Line(points={{-34,-70},{-34,-62}}, color={0,127,255}));
  connect(R12.port_b, HB2.port_a)
    annotation (Line(points={{42,-28},{42,-24}}, color={0,127,255}));
  connect(HB2.port_b, R13.port_a)
    annotation (Line(points={{42,-8},{42,2},{40,2}}, color={0,127,255}));
  connect(R13.port_b, T4S.port_a)
    annotation (Line(points={{30,2},{26,2},{26,20}}, color={0,127,255}));
  connect(R13.port_b, T4D.port_a)
    annotation (Line(points={{30,2},{8,2}}, color={0,127,255}));
  connect(R15.port_b, T5S.port_a) annotation (Line(points={{-54,2},{-73,2},{-73,
          20},{-72,20}}, color={0,127,255}));
  connect(R15.port_b, T5D.port_a)
    annotation (Line(points={{-54,2},{-80,2}}, color={0,127,255}));
  connect(U3.port_b, D_A3.port_a)
    annotation (Line(points={{-120,2},{-122,2}}, color={0,127,255}));
  connect(U3.port_a, T5D.port_b)
    annotation (Line(points={{-106,2},{-100,2}}, color={0,127,255}));
  connect(D_A3.port_b, V5.port_a)
    annotation (Line(points={{-134,2},{-136,2}}, color={0,127,255}));
  connect(V5.port_b, D_H3.port_a)
    annotation (Line(points={{-148,2},{-150,2}}, color={0,127,255}));
  connect(YONOS.port_a, D_H3.port_b)
    annotation (Line(points={{-164,2},{-162,2}}, color={0,127,255}));
  connect(YONOS.port_b, V6.port_a)
    annotation (Line(points={{-184,2},{-188,2}}, color={0,127,255}));
  connect(H2.port_b, R8.port_a)
    annotation (Line(points={{-34,-274},{-34,-264}}, color={0,127,255}));
  connect(H1.port_b, R7.port_a)
    annotation (Line(points={{42,-276},{42,-264}}, color={0,127,255}));
  connect(D_B3.port_b, E4.port_a)
    annotation (Line(points={{-234,2},{-240,2},{-240,20}}, color={0,127,255}));
  connect(V6.port_b, U4.port_a)
    annotation (Line(points={{-200,2},{-206,2}}, color={0,127,255}));
  connect(D_B3.port_a, U4.port_b)
    annotation (Line(points={{-222,2},{-218,2}}, color={0,127,255}));
  connect(SINK.ports[1], C1.port_b) annotation (Line(points={{274,143.333},{270,
          143.333},{270,146},{266,146}}, color={0,127,255}));
  connect(K2_R.port_b, C1.port_a)
    annotation (Line(points={{240,146},{246,146}}, color={0,127,255}));
  connect(K4_R.port_b, C2.port_a)
    annotation (Line(points={{244,226},{248,226}}, color={0,127,255}));
  connect(C2.port_b, SINK.ports[2]) annotation (Line(points={{268,226},{272,226},
          {272,146},{274,146}}, color={0,127,255}));
  connect(K6_R.port_b, C3.port_a)
    annotation (Line(points={{242,308},{246,308}}, color={0,127,255}));
  connect(C3.port_b, SINK.ports[3]) annotation (Line(points={{266,308},{274,308},
          {274,148.667}}, color={0,127,255}));
  connect(R11.port_b, T3_2.port_a)
    annotation (Line(points={{8,-61},{8,-60},{12,-60}}, color={0,127,255}));
  connect(T3_2.port_b, R12.port_a)
    annotation (Line(points={{32,-60},{32,-42},{42,-42}}, color={0,127,255}));
  connect(T3_1.port_b, R12.port_a)
    annotation (Line(points={{42,-50},{42,-42}}, color={0,127,255}));
  connect(Q_floor5.V_flow, y_v_5)
    annotation (Line(points={{160,297},{160,280},{314,280}}, color={0,0,127}));
  connect(Q_floor3.V_flow, y_v_3)
    annotation (Line(points={{160,215},{160,200},{314,200}}, color={0,0,127}));
  connect(Q_floor1.V_flow, y_v_1)
    annotation (Line(points={{160,135},{160,120},{314,120}}, color={0,0,127}));
  connect(GF80_1.port_b, pressure.port)
    annotation (Line(points={{42,-144},{70,-144}}, color={0,127,255}));
  connect(GF80_1.port_a, pressure1.port)
    annotation (Line(points={{42,-168},{70,-168}}, color={0,127,255}));
  connect(pressure.p, add.u1) annotation (Line(points={{81,-134},{86,-134},{86,
          -140},{94,-140}}, color={0,0,127}));
  connect(pressure1.p, add.u2) annotation (Line(points={{81,-158},{86,-158},{86,
          -152},{94,-152}}, color={0,0,127}));
  connect(add.y, y_p_1)
    annotation (Line(points={{117,-146},{314,-146}}, color={0,0,127}));
  connect(YONOS.port_b, pressure2.port)
    annotation (Line(points={{-184,2},{-184,-17}}, color={0,127,255}));
  connect(YONOS.port_a, pressure3.port)
    annotation (Line(points={{-164,2},{-164,-17}}, color={0,127,255}));
  connect(pressure2.p, add1.u2) annotation (Line(points={{-177,-24.7},{-177,
          -28.35},{-169.6,-28.35},{-169.6,-30.8}}, color={0,0,127}));
  connect(pressure3.p, add1.u1) annotation (Line(points={{-157,-24.7},{-157,
          -27.35},{-162.4,-27.35},{-162.4,-30.8}}, color={0,0,127}));
  connect(add1.y, y_p_2) annotation (Line(points={{-166,-44.6},{-166,-48},{314,
          -48}}, color={0,0,127}));
  connect(y_p_1, y_p_1)
    annotation (Line(points={{314,-146},{314,-146}}, color={0,0,127}));
  connect(H8.port_b, SINK1.ports[1]) annotation (Line(points={{-74,-58},{-90,
          -58},{-90,-105.333},{-100,-105.333}}, color={0,127,255}));
  connect(H9.port_b, SINK1.ports[2]) annotation (Line(points={{-2,-114},{-50,
          -114},{-50,-108},{-100,-108}}, color={0,127,255}));
  connect(H10.port_b, SINK1.ports[3]) annotation (Line(points={{-154,-70},{-84,
          -70},{-84,-110.667},{-100,-110.667}}, color={0,127,255}));
  connect(H8.port_a, R10.port_b) annotation (Line(points={{-62,-58},{-48,-58},{
          -48,-70},{-34,-70}}, color={0,127,255}));
  connect(H9.port_a, R9.port_b) annotation (Line(points={{10,-114},{26,-114},{
          26,-70},{42,-70}}, color={0,127,255}));
  connect(H10.port_a, D_B3.port_b) annotation (Line(points={{-166,-70},{-234,
          -70},{-234,2}}, color={0,127,255}));
  connect(u_v_5, Valve_floor5.opening) annotation (Line(points={{-300,330},{190,
          330},{190,316}}, color={0,0,127}));
  connect(u_v_3, Valve_floor3.opening) annotation (Line(points={{-300,250},{190,
          250},{190,234}}, color={0,0,127}));
  connect(u_v_1, Valve_floor1.opening) annotation (Line(points={{-300,170},{184,
          170},{184,154}}, color={0,0,127}));
  connect(u_p_2, YONOS.N_in)
    annotation (Line(points={{-300,54},{-174,54},{-174,12}}, color={0,0,127}));
  connect(u_p_1, GF80_2.N_in) annotation (Line(points={{-298,-150},{-172,-150},
          {-172,-156},{-46,-156}}, color={0,0,127}));
  connect(u_p_1, GF80_1.N_in) annotation (Line(points={{-298,-150},{-172,-150},
          {-172,-144},{18,-144},{18,-156},{30,-156}}, color={0,0,127}));
  annotation (
    Icon(coordinateSystem(preserveAspectRatio=false, extent={{-280,-380},{300,340}})),
    Diagram(coordinateSystem(preserveAspectRatio=false, extent={{-280,-380},{300,
            340}})),
    uses(Modelica(version="3.2.2")));
end Hochhaus;
