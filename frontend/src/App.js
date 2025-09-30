import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import '@/App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const App = () => {
  const [activeTab, setActiveTab] = useState('inventario');
  const [productos, setProductos] = useState([]);
  const [contactos, setContactos] = useState([]);
  const [alertas, setAlertas] = useState([]);
  const [configuracion, setConfiguracion] = useState({ stock_bajo_limite: 10, vencimiento_alerta_meses: 2 });
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [modalType, setModalType] = useState(''); // 'producto' o 'contacto'
  const [editingItem, setEditingItem] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Estados para el formulario de producto
  const [productoForm, setProductoForm] = useState({
    codigo: '',
    descripcion: '',
    unidad_venta: 'Unidades',
    stock_actual: 0,
    precio_venta: 0,
    fecha_ingreso: '',
    fecha_vencimiento: ''
  });

  // Estados para el formulario de contacto
  const [contactoForm, setContactoForm] = useState({
    nombre: '',
    direccion: '',
    telefono: '',
    correo: '',
    tipo: 'Proveedor'
  });

  // Cargar datos iniciales
  useEffect(() => {
    cargarDatos();
  }, []);

  const cargarDatos = async () => {
    setLoading(true);
    try {
      const [productosRes, contactosRes, alertasRes, configRes] = await Promise.all([
        axios.get(`${API}/productos`),
        axios.get(`${API}/contactos`),
        axios.get(`${API}/alertas`),
        axios.get(`${API}/configuracion`)
      ]);
      
      setProductos(productosRes.data);
      setContactos(contactosRes.data);
      setAlertas(alertasRes.data);
      setConfiguracion(configRes.data);
    } catch (error) {
      console.error('Error cargando datos:', error);
    } finally {
      setLoading(false);
    }
  };

  // Función para obtener el color de fila según las alertas
  const getRowColor = (producto) => {
    if (producto.stock_actual === 0) return 'bg-red-100 border-red-300';
    if (producto.stock_actual < configuracion.stock_bajo_limite) return 'bg-yellow-100 border-yellow-300';
    
    if (producto.fecha_vencimiento) {
      const fechaVencimiento = new Date(producto.fecha_vencimiento);
      const fechaLimite = new Date();
      fechaLimite.setMonth(fechaLimite.getMonth() + configuracion.vencimiento_alerta_meses);
      
      if (fechaVencimiento <= fechaLimite) return 'bg-orange-100 border-orange-300';
    }
    
    return 'bg-white border-gray-200';
  };

  // Productos filtrados
  const productosFiltrados = useMemo(() => {
    return productos.filter(producto => 
      producto.codigo.toLowerCase().includes(searchTerm.toLowerCase()) ||
      producto.descripcion.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [productos, searchTerm]);

  // Contactos filtrados
  const contactosFiltrados = useMemo(() => {
    return contactos.filter(contacto => 
      contacto.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (contacto.correo && contacto.correo.toLowerCase().includes(searchTerm.toLowerCase()))
    );
  }, [contactos, searchTerm]);

  // Manejar envío del formulario de producto
  const handleProductoSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const data = {
        ...productoForm,
        stock_actual: parseInt(productoForm.stock_actual) || 0,
        precio_venta: parseFloat(productoForm.precio_venta) || 0,
        fecha_ingreso: productoForm.fecha_ingreso || null,
        fecha_vencimiento: productoForm.fecha_vencimiento || null
      };

      if (editingItem) {
        await axios.put(`${API}/productos/${editingItem.id}`, data);
      } else {
        await axios.post(`${API}/productos`, data);
      }
      
      setShowModal(false);
      setEditingItem(null);
      resetProductoForm();
      await cargarDatos();
    } catch (error) {
      console.error('Error guardando producto:', error);
      alert('Error guardando producto');
    } finally {
      setLoading(false);
    }
  };

  // Manejar envío del formulario de contacto
  const handleContactoSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      if (editingItem) {
        await axios.put(`${API}/contactos/${editingItem.id}`, contactoForm);
      } else {
        await axios.post(`${API}/contactos`, contactoForm);
      }
      
      setShowModal(false);
      setEditingItem(null);
      resetContactoForm();
      await cargarDatos();
    } catch (error) {
      console.error('Error guardando contacto:', error);
      alert('Error guardando contacto');
    } finally {
      setLoading(false);
    }
  };

  // Eliminar producto
  const eliminarProducto = async (id) => {
    if (window.confirm('¿Estás seguro de eliminar este producto?')) {
      try {
        await axios.delete(`${API}/productos/${id}`);
        await cargarDatos();
      } catch (error) {
        console.error('Error eliminando producto:', error);
        alert('Error eliminando producto');
      }
    }
  };

  // Eliminar contacto
  const eliminarContacto = async (id) => {
    if (window.confirm('¿Estás seguro de eliminar este contacto?')) {
      try {
        await axios.delete(`${API}/contactos/${id}`);
        await cargarDatos();
      } catch (error) {
        console.error('Error eliminando contacto:', error);
        alert('Error eliminando contacto');
      }
    }
  };

  // Editar item
  const editarItem = (item, tipo) => {
    setEditingItem(item);
    setModalType(tipo);
    
    if (tipo === 'producto') {
      setProductoForm({
        codigo: item.codigo || '',
        descripcion: item.descripcion || '',
        unidad_venta: item.unidad_venta || 'Unidades',
        stock_actual: item.stock_actual || 0,
        precio_venta: item.precio_venta || 0,
        fecha_ingreso: item.fecha_ingreso || '',
        fecha_vencimiento: item.fecha_vencimiento || ''
      });
    } else {
      setContactoForm({
        nombre: item.nombre || '',
        direccion: item.direccion || '',
        telefono: item.telefono || '',
        correo: item.correo || '',
        tipo: item.tipo || 'Proveedor'
      });
    }
    
    setShowModal(true);
  };

  // Abrir modal para nuevo item
  const abrirModalNuevo = (tipo) => {
    setEditingItem(null);
    setModalType(tipo);
    if (tipo === 'producto') {
      resetProductoForm();
    } else {
      resetContactoForm();
    }
    setShowModal(true);
  };

  const resetProductoForm = () => {
    setProductoForm({
      codigo: '',
      descripcion: '',
      unidad_venta: 'Unidades',
      stock_actual: 0,
      precio_venta: 0,
      fecha_ingreso: '',
      fecha_vencimiento: ''
    });
  };

  const resetContactoForm = () => {
    setContactoForm({
      nombre: '',
      direccion: '',
      telefono: '',
      correo: '',
      tipo: 'Proveedor'
    });
  };

  // Actualizar configuración
  const actualizarConfiguracion = async (nuevaConfig) => {
    try {
      await axios.put(`${API}/configuracion`, nuevaConfig);
      setConfiguracion(prev => ({ ...prev, ...nuevaConfig }));
      await cargarDatos(); // Recargar para actualizar alertas
    } catch (error) {
      console.error('Error actualizando configuración:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <h1 className="text-2xl font-bold text-gray-900">📦 Gestión de Inventario</h1>
            <div className="text-sm text-gray-500">
              Total productos: {productos.length} | Alertas: {alertas.length}
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: 'inventario', label: '📊 Inventario', count: productos.length },
              { id: 'contactos', label: '👥 Contactos', count: contactos.length },
              { id: 'alertas', label: '⚠️ Alertas', count: alertas.length },
              { id: 'configuracion', label: '⚙️ Configuración' }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label} {tab.count !== undefined && `(${tab.count})`}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Inventario Tab */}
        {activeTab === 'inventario' && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <div className="flex items-center space-x-4">
                <input
                  type="text"
                  placeholder="Buscar productos..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <div className="text-sm text-gray-500">
                  Mostrando {productosFiltrados.length} productos
                </div>
              </div>
              <button
                onClick={() => abrirModalNuevo('producto')}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                ➕ Nuevo Producto
              </button>
            </div>

            {/* Leyenda de colores */}
            <div className="mb-4 flex flex-wrap gap-4 text-sm">
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 bg-red-100 border border-red-300 rounded"></div>
                <span>Stock agotado</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 bg-yellow-100 border border-yellow-300 rounded"></div>
                <span>Stock bajo</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 bg-orange-100 border border-orange-300 rounded"></div>
                <span>Próximo a vencer</span>
              </div>
            </div>

            {/* Tabla de productos */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Código</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Descripción</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Unidad</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stock</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Precio</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">F. Ingreso</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">F. Vencimiento</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {productosFiltrados.map((producto) => (
                      <tr key={producto.id} className={`${getRowColor(producto)} hover:bg-opacity-75 transition-colors`}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{producto.codigo}</td>
                        <td className="px-6 py-4 text-sm text-gray-900">{producto.descripcion}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{producto.unidad_venta}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <span className={producto.stock_actual === 0 ? 'text-red-600' : producto.stock_actual < configuracion.stock_bajo_limite ? 'text-yellow-600' : 'text-gray-900'}>
                            {producto.stock_actual}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${producto.precio_venta.toFixed(2)}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {producto.fecha_ingreso ? new Date(producto.fecha_ingreso).toLocaleDateString() : '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {producto.fecha_vencimiento ? new Date(producto.fecha_vencimiento).toLocaleDateString() : '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                          <button
                            onClick={() => editarItem(producto, 'producto')}
                            className="text-blue-600 hover:text-blue-900 transition-colors"
                          >
                            ✏️ Editar
                          </button>
                          <button
                            onClick={() => eliminarProducto(producto.id)}
                            className="text-red-600 hover:text-red-900 transition-colors"
                          >
                            🗑️ Eliminar
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {productosFiltrados.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    No se encontraron productos
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Contactos Tab */}
        {activeTab === 'contactos' && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <div className="flex items-center space-x-4">
                <input
                  type="text"
                  placeholder="Buscar contactos..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <div className="text-sm text-gray-500">
                  Mostrando {contactosFiltrados.length} contactos
                </div>
              </div>
              <button
                onClick={() => abrirModalNuevo('contacto')}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
              >
                ➕ Nuevo Contacto
              </button>
            </div>

            {/* Tabla de contactos */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Teléfono</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Correo</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Dirección</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {contactosFiltrados.map((contacto) => (
                      <tr key={contacto.id} className="hover:bg-gray-50 transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{contacto.nombre}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            contacto.tipo === 'Proveedor' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'
                          }`}>
                            {contacto.tipo}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{contacto.telefono || '-'}</td>
                        <td className="px-6 py-4 text-sm text-gray-500">{contacto.correo || '-'}</td>
                        <td className="px-6 py-4 text-sm text-gray-500">{contacto.direccion || '-'}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                          <button
                            onClick={() => editarItem(contacto, 'contacto')}
                            className="text-blue-600 hover:text-blue-900 transition-colors"
                          >
                            ✏️ Editar
                          </button>
                          <button
                            onClick={() => eliminarContacto(contacto.id)}
                            className="text-red-600 hover:text-red-900 transition-colors"
                          >
                            🗑️ Eliminar
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {contactosFiltrados.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    No se encontraron contactos
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Alertas Tab */}
        {activeTab === 'alertas' && (
          <div>
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">📋 Panel de Recordatorios</h2>
              <p className="text-gray-600">Productos que requieren atención inmediata</p>
            </div>

            {/* Alertas por categoría */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <h3 className="text-lg font-medium text-red-900 mb-2">🚨 Stock Agotado</h3>
                <div className="text-2xl font-bold text-red-600 mb-2">
                  {alertas.filter(a => a.tipo_alerta === 'stock_cero').length}
                </div>
                <p className="text-red-700 text-sm">Productos sin stock</p>
              </div>
              
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <h3 className="text-lg font-medium text-yellow-900 mb-2">⚠️ Stock Bajo</h3>
                <div className="text-2xl font-bold text-yellow-600 mb-2">
                  {alertas.filter(a => a.tipo_alerta === 'stock_bajo').length}
                </div>
                <p className="text-yellow-700 text-sm">Menos de {configuracion.stock_bajo_limite} unidades</p>
              </div>
              
              <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                <h3 className="text-lg font-medium text-orange-900 mb-2">⏰ Próximo a Vencer</h3>
                <div className="text-2xl font-bold text-orange-600 mb-2">
                  {alertas.filter(a => a.tipo_alerta === 'proximo_vencer').length}
                </div>
                <p className="text-orange-700 text-sm">En {configuracion.vencimiento_alerta_meses} meses</p>
              </div>
            </div>

            {/* Lista detallada de alertas */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Detalle de Alertas</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Código</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Descripción</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stock</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">F. Vencimiento</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Días</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {alertas.map((alerta, index) => {
                      const bgColor = alerta.tipo_alerta === 'stock_cero' ? 'bg-red-50' :
                                     alerta.tipo_alerta === 'stock_bajo' ? 'bg-yellow-50' : 'bg-orange-50';
                      const textColor = alerta.tipo_alerta === 'stock_cero' ? 'text-red-800' :
                                       alerta.tipo_alerta === 'stock_bajo' ? 'text-yellow-800' : 'text-orange-800';
                      
                      return (
                        <tr key={index} className={`${bgColor} hover:bg-opacity-75 transition-colors`}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <span className={`px-2 py-1 text-xs rounded-full ${bgColor} ${textColor}`}>
                              {alerta.tipo_alerta === 'stock_cero' ? '🚨 Agotado' :
                               alerta.tipo_alerta === 'stock_bajo' ? '⚠️ Bajo' : '⏰ Vence'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{alerta.codigo}</td>
                          <td className="px-6 py-4 text-sm text-gray-900">{alerta.descripcion}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <span className={alerta.stock_actual === 0 ? 'text-red-600' : 'text-yellow-600'}>
                              {alerta.stock_actual}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {alerta.fecha_vencimiento ? new Date(alerta.fecha_vencimiento).toLocaleDateString() : '-'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {alerta.dias_para_vencer !== null ? `${alerta.dias_para_vencer} días` : '-'}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                {alertas.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    🎉 ¡No hay alertas! Todo está bajo control.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Configuración Tab */}
        {activeTab === 'configuracion' && (
          <div>
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">⚙️ Configuración del Sistema</h2>
              <p className="text-gray-600">Ajusta los umbrales de alertas para tu negocio</p>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    📉 Límite de Stock Bajo
                  </label>
                  <div className="flex items-center space-x-3">
                    <input
                      type="number"
                      min="0"
                      value={configuracion.stock_bajo_limite}
                      onChange={(e) => {
                        const value = parseInt(e.target.value) || 0;
                        actualizarConfiguracion({ stock_bajo_limite: value });
                      }}
                      className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <span className="text-sm text-gray-500">unidades</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Los productos con stock menor a este valor se marcarán en amarillo
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    📅 Alerta de Vencimiento
                  </label>
                  <div className="flex items-center space-x-3">
                    <input
                      type="number"
                      min="1"
                      value={configuracion.vencimiento_alerta_meses}
                      onChange={(e) => {
                        const value = parseInt(e.target.value) || 1;
                        actualizarConfiguracion({ vencimiento_alerta_meses: value });
                      }}
                      className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <span className="text-sm text-gray-500">meses</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Los productos que venzan en este período se marcarán en naranja
                  </p>
                </div>
              </div>

              <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                <h3 className="text-sm font-medium text-blue-900 mb-2">💡 Consejos</h3>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• Ajusta el límite de stock bajo según tu rotación de productos</li>
                  <li>• La alerta de vencimiento te ayuda a priorizar las ventas</li>
                  <li>• Los cambios se aplican inmediatamente en toda la aplicación</li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Modal para formularios */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">
                {editingItem ? 'Editar' : 'Nuevo'} {modalType === 'producto' ? 'Producto' : 'Contacto'}
              </h3>
            </div>
            
            <form onSubmit={modalType === 'producto' ? handleProductoSubmit : handleContactoSubmit}>
              <div className="px-6 py-4 space-y-4">
                {modalType === 'producto' ? (
                  // Formulario de producto
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Código *</label>
                      <input
                        type="text"
                        required
                        value={productoForm.codigo}
                        onChange={(e) => setProductoForm(prev => ({ ...prev, codigo: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Descripción *</label>
                      <input
                        type="text"
                        required
                        value={productoForm.descripcion}
                        onChange={(e) => setProductoForm(prev => ({ ...prev, descripcion: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Unidad de Venta</label>
                      <select
                        value={productoForm.unidad_venta}
                        onChange={(e) => setProductoForm(prev => ({ ...prev, unidad_venta: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      >
                        <option value="Unidades">Unidades</option>
                        <option value="Cajas">Cajas</option>
                      </select>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Stock Actual</label>
                        <input
                          type="number"
                          min="0"
                          value={productoForm.stock_actual}
                          onChange={(e) => setProductoForm(prev => ({ ...prev, stock_actual: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Precio de Venta</label>
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          value={productoForm.precio_venta}
                          onChange={(e) => setProductoForm(prev => ({ ...prev, precio_venta: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Fecha de Ingreso</label>
                        <input
                          type="date"
                          value={productoForm.fecha_ingreso}
                          onChange={(e) => setProductoForm(prev => ({ ...prev, fecha_ingreso: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Fecha de Vencimiento</label>
                        <input
                          type="date"
                          value={productoForm.fecha_vencimiento}
                          onChange={(e) => setProductoForm(prev => ({ ...prev, fecha_vencimiento: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>
                    </div>
                  </>
                ) : (
                  // Formulario de contacto
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Nombre *</label>
                      <input
                        type="text"
                        required
                        value={contactoForm.nombre}
                        onChange={(e) => setContactoForm(prev => ({ ...prev, nombre: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Tipo</label>
                      <select
                        value={contactoForm.tipo}
                        onChange={(e) => setContactoForm(prev => ({ ...prev, tipo: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      >
                        <option value="Proveedor">Proveedor</option>
                        <option value="Tienda">Tienda</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Teléfono</label>
                      <input
                        type="tel"
                        value={contactoForm.telefono}
                        onChange={(e) => setContactoForm(prev => ({ ...prev, telefono: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Correo Electrónico</label>
                      <input
                        type="email"
                        value={contactoForm.correo}
                        onChange={(e) => setContactoForm(prev => ({ ...prev, correo: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Dirección</label>
                      <textarea
                        value={contactoForm.direccion}
                        onChange={(e) => setContactoForm(prev => ({ ...prev, direccion: e.target.value }))}
                        rows={3}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                  </>
                )}
              </div>
              
              <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowModal(false);
                    setEditingItem(null);
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
                >
                  {loading ? 'Guardando...' : (editingItem ? 'Actualizar' : 'Crear')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Loading overlay */}
      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-25 flex items-center justify-center z-40">
          <div className="bg-white p-4 rounded-lg">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-sm text-gray-600">Cargando...</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;
